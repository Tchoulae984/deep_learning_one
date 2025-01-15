import face_recognition

# Load the images
known_image = face_recognition.load_image_file('local_img/iamge2.jpg')
unknown_image = face_recognition.load_image_file('local_img/image.jpg')

# Encode the faces
biden_encoding = face_recognition.face_encodings(known_image)[0]
unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

# Compare the faces
results = face_recognition.compare_faces([biden_encoding], unknown_encoding)

# Print the result
print(str(results))
