from flask import Flask, render_template, request
import os
import face_recognition

#Creation de l'application web Flask
app = Flask(__name__)

#Route pour la page d'accueil
@app.route ('/', methods = ['GET', 'POST'])
def index():
    return 'API face recognition'

#Compare deux image (interface)
@app.route ('/compare', methods=['GET', 'POST'])
def compare():
    return render_template('compare.html')




#recuperation del 'image 1 et enregistrement
@app.route ('/image1', methods=['POST'])
def image1():
    
    if os.path.exists('image_new1.jpg'):
        os.remove('image_new1.jpg')
        
    image1 = request.files['image1']
    image1.save('local_img/image_new1.jpg')
    
    return "Enregsitrer avec success"

#recuperation del 'image 1 et enregistrement
@app.route ('/image2', methods=['POST'])
def image2():
    
    if os.path.exists('image_new2.jpg'):
        os.remove('image_new2.jpg')
        
    image2 = request.files['image2']
    image2.save('local_img/image_new2.jpg')
    
    return "Enregsitrer avec success"






#Predict de l'image 2 par rapport a l'image 1
@app.route ('/predict', methods=['POST'])
def predict():
    
    #REcuperation de l'image 1
    if os.path.exists('local_img/image_new1.jpg'):
        os.remove('local_img/image_new1.jpg')
        
    image1 = request.files['image1']
    image1.save('local_img/image_new1.jpg')
    
    #Recuperation de l'image 2
    if os.path.exists('local_img/image_new2.jpg'):
        os.remove('local_img/image_new2.jpg')
        
    image2 = request.files['image2']
    image2.save('local_img/image_new2.jpg')
    
    #-------------------------------------------------
    
    
    # Load the images
    known_image = face_recognition.load_image_file('local_img/image_new1.jpg')
    unknown_image = face_recognition.load_image_file('local_img/image_new2.jpg')

    # Encode the faces
    biden_encoding = face_recognition.face_encodings(known_image)[0]
    unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

    # Compare the faces
    results = face_recognition.compare_faces([biden_encoding], unknown_encoding)

    # Print the result
    return str(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 8047)