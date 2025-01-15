import requests
from fastapi import FastAPI, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict
import mysql.connector
from mysql.connector import pooling
import uuid
import json
import os
import datetime
from datetime import datetime, timedelta
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Database connection pooling configuration
dbconfig = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

# Configure connection pooling with a pool size of 5 connections
connection_pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **dbconfig)

# Dependency to provide a database connection from the pool for each request
def get_db_connection():
    connection = connection_pool.get_connection()
    try:
        connection.ping(reconnect=True, attempts=3, delay=5)  # Ensure the connection is active
        yield connection
    finally:
        connection.close()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    #allow_origins=["http://localhost:5173", "https://affordring.com", "https://users.affordring.com", "http://192.168.1.102:5173"],  # Update this to the URL of your frontend
   allow_origins=["*"],  # Update this to the URL of your frontend
    #allow_origins=[ "https://affordring.com", "https://users.affordring.com"],  # Update this to the URL of your frontend

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define data models



# API Endpoints


# Function to get city, region, and country from IP address
def get_location_from_ip(ip_address):
    print("fecthing")
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}?token=fdf68ada0b9f62")
        response.raise_for_status()
        data = response.json()

        city = data.get("city")
        region = data.get("region")
        country = data.get("country")
        print (ip_address, 'is staying in', region)
        return city, region, country
    except Exception as e:
        print(f"Error fetching location data: {e}")
        return None, None, None
    '''try:
        response = requests.get(f"https://ipwho.is/{ip_address}")
        response.raise_for_status()  # Ensure a valid response
        location_data = response.json()

        city = location_data.get("city")
        region = location_data.get("region")
        country = location_data.get("country")
        return city, region, country
    except Exception as e:
        print("Error fetching location data:", e)
        return None, None, None'''

# Generate a unique session ID
class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    city: Optional[str]  
    region: Optional[str]  
    country: Optional[str]  



@app.post("/start_session/", response_model=SessionResponse)
async def start_session(request: Request, db=Depends(get_db_connection), user_id: Optional[str] = None):
    # Reuse the provided user_id if available, otherwise generate a new one
    if not user_id:
        user_id = str(uuid.uuid4())

    user_ip = request.client.host
    city, region, country = get_location_from_ip(user_ip)

    cursor = db.cursor()
    try:
        # Ensure user exists in the database
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

        if not result:
            cursor.execute(
                "INSERT INTO users (user_id, city, region, country, created_at) VALUES (%s, %s, %s, %s, %s)",
                (user_id, city, region, country, datetime.now())
            )

        # Generate a new session ID with 30-minute expiration
        session_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO sessions (session_id, user_id, created_at) VALUES (%s, %s, %s)",
            (session_id, user_id, datetime.now())
        )
        db.commit()
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()

    response = JSONResponse(content={"session_id": session_id, "user_id": user_id, "city": city, "region": region, "country": country})
    expiration_time = timedelta(minutes=30)  # Session expires after 30 minutes
    response.set_cookie(key="user_id", value=user_id, max_age=expiration_time.total_seconds(), httponly=True)
    return response





# Define the data model for the log event
class LogEventModel(BaseModel):
    session_id: str
    event_type: str
    event_target: Optional[str] = None
    additional_data: Optional[Dict] = None

# Endpoint to log events
@app.post("/log_event/")
async def log_event(event: LogEventModel, db=Depends(get_db_connection)):
    # Convert additional_data to JSON string if provided
    additional_data = json.dumps(event.additional_data) if event.additional_data else "{}"
    
    # Insert data into the database
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO events (session_id, event_type, event_target, additional_data) VALUES (%s, %s, %s, %s)",
            (event.session_id, event.event_type, event.event_target, additional_data)
        )
        db.commit()
        return {"status": "success", "event_logged": event.event_type}
    except mysql.connector.Error as e:
        db.rollback()
        print(f"Error inserting data: {e}")
        raise HTTPException(status_code=500, detail="Failed to log event")
    finally:
        cursor.close()




class SearchTermRequest(BaseModel):
    term: str

# Path to the JSON file where search terms will be saved
FILE_PATH = "search_terms.json"

@app.post("/save_search")
async def save_search(search_request: SearchTermRequest):
    search_term = search_request.term

    if not search_term:
        return {"error": "Search term is empty or invalid"}

    if not os.path.exists(os.path.dirname(FILE_PATH)) and os.path.dirname(FILE_PATH):
        os.makedirs(os.path.dirname(FILE_PATH))

    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r") as file:
            search_data = json.load(file)
    else:
        search_data = []

    search_data.append(search_term)
    with open(FILE_PATH, "w") as file:
        json.dump(search_data, file, indent=4)

    return {"message": "Search term saved successfully"}


# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
