from __future__ import print_function
import cv2 as cv
import argparse



profileface_path= "haarcascades/haarcascade_frontalcatface.xml"
profileface_cascade = cv.CascadeClassifier()
#-- 1. Load the cascades
if not profileface_cascade.load(cv.samples.findFile(profileface_path)):
    print('--(!)Error loading face cascade')
    exit(0)


cap = cv.VideoCapture(2)
if not cap.isOpened:
    print('--(!)Error opening video capture')
    exit(0)
while True:
    ret, frame = cap.read()
    frame_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    frame_gray = cv.equalizeHist(frame_gray)
    #-- Detect faces
    faces = profileface_cascade.detectMultiScale(frame_gray)
    for (x,y,w,h) in faces:
        center = (x + w//2, y + h//2)
        frame = cv.rectangle(frame,(x,w),(y,h),(0,255,0),2)
        # faceROI = frame_gray[y:y+h,x:x+w]
        #-- In each face, detect eyes
        # v2.rectangle(img,(x1,y1),(x2,y2),(0,255,0),2)

    cv.imshow('Capture - Face detection', frame)
    if frame is None:
        print('--(!) No captured frame -- Break!')
        break
    if cv.waitKey(10) == 27:
        break

cap.release()
cv2.destroyAllWindows()