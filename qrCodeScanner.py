import cv2
import numpy as np
from pyzbar.pyzbar import decode
cap = cv2.VideoCapture(0)
cap.set(3,640)
cap.set(4,480)

with open('hostel_idFile.text') as f:
    hostel_idList = f.read().splitlines()

while True:

    success, img = cap.read()
    for barcode in decode(img):
        hostel_id = barcode.data.decode('utf-8')
        print(hostel_id)

        if hostel_id in hostel_idList:
            myOutput = 'Authorized'
            myColor = (0,255,0)
        else:
            myOutput = 'Un-Authorized'
            myColor = (0, 0, 255)

        pts = np.array([barcode.polygon],np.int32)
        pts = pts.reshape((-1,1,2))
        cv2.polylines(img,[pts],True,myColor,5)
        pts2 = barcode.rect
        cv2.putText(img,myOutput,(pts2[0],pts2[1]),cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,myColor,2)

    cv2.imshow('Result',img)
    cv2.waitKey(1)
