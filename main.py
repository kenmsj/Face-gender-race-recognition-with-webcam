""""
main is the main routine for face recognition project.
After installing the requirements, plug in your webcam and run main.py.
Preprocesses are needed to define some IDs for face identification.

By H.Iman
"""
import tensorflow as tf
import align.detect_face
import cv2
import numpy as np
import pickle
import os
from threading import Thread
from face_tracking1.face_tracking import *
from gender.pred import *
from thread_with_return import ThreadWithReturnValue
from gender_and_race import gender_race_detector
import face_model
import argparse

def track_and_show(video_capture):
    """"
    track_and_show draws bounding boxes for any detected face
    and tracks it.
    """
    event_interval = 2
    pipeline = Pipeline(event_interval=event_interval)
    while True:
        ret, frame = video_capture.read() # Read video from webcam
        try:
            # Detect faces OR track the detected face. 
            boxes, detected_new = pipeline.boxes_for_frame(frame)
            color = GREEN
            # Draw bounding boxes (and race, gender and Name) for every detected face.
            draw_boxes(frame, boxes,best_name,color,best_class_probabilities,race,gender)
            print('22222222222222222222222222222222')
            cv2.imshow('Video1', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except:
            print("An exception in track_and_show occurred")

def detect_align_recognize(video_capture, pnet, rnet, onet,model, class_names, clf, labels,arcface_model):
    """"
    detect_align_recognize detects faces in the frame, recognizes
    the person
    """
    # Face detection parameters
    minsize = 30
    threshold1 = [0.6, 0.7, 0.7]
    factor1 = 0.709
    input_image_size = 160

    # Global variables that we 
    global best_class_probabilities
    global race
    global gender
    global best_name
    best_name = ['', '']

    while True:
        ret, frame = video_capture.read()
        try:
            # Extract features from faces using arcface loss.
            emb_array, single_face_locations = arcface_model.get_input(frame, arcface_model) #,faces_from_faceboxes
            # print(boxes)
            # Compare face features with features stored in the database.
            predictions = model.predict_proba(emb_array)
            print(predictions)
            best_class_indices = np.argmax(predictions, axis=1)
            best_class_probabilities = predictions[np.arange(len(best_class_indices)), best_class_indices]
            for i in range(len(best_class_indices)):
                best_name[i] = class_names[best_class_indices[i]]
            
            # Determine each face's gender and race. 
            # gender: Male, Female
            # race: White, Black, Asian
            race, gender = gender_race_detector(single_face_locations, labels, clf, frame)
            print('1111111111111111111111111111111')
        except:
            pass

def main(args):
    arcface_model = face_model.FaceModel(args)
    gender_model = 'gender/face_model.pkl'
    with open(gender_model,'rb') as f:
        clf, labels = pickle.load(f,encoding='latin1')
    video_capture = cv2.VideoCapture(0)
    classifier_path ="trained_classifier/classifier.pkl"
    with open(classifier_path, 'rb') as f:
        (model, class_names) = pickle.load(f)
        print("Loaded classifier file")

    with tf.Graph().as_default():
        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=.7)
        sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options, log_device_placement=False))
        with sess.as_default():
            # Bounding box
            pnet, rnet, onet = align.detect_face.create_mtcnn(sess, "align")

    # Using two threads, one for recognition, the other for detecton, tracking and showing the results
    p1 = ThreadWithReturnValue(target = detect_align_recognize, args=(video_capture, pnet, rnet, onet,model,class_names, clf, labels,arcface_model, ))
    p2 = ThreadWithReturnValue(target = track_and_show, args=(video_capture,))#, clf, labels

    p1.start()
    p2.start()

    p1.join()
    p2.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='face model test')
    parser.add_argument('--image-size', default='112,112', help='')
    parser.add_argument('--model', default='models/model-r100-ii/model,0', help='path to load model.')
    parser.add_argument('--ga-model', default='gender-age/model/model,0', help='path to load model.')
    parser.add_argument('--gpu', default=0, type=int, help='gpu id') # ------
    parser.add_argument('--det', default=0, type=int, help='mtcnn option, 1 means using R+O, 0 means detect from begining') # ------
    parser.add_argument('--flip', default=0, type=int, help='whether do lr flip aug') # --------
    parser.add_argument('--threshold', default=1.24, type=float, help='ver dist threshold') #------
    args = parser.parse_args()
    main(args)
