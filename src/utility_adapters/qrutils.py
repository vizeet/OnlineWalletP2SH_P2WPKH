# -*- coding: utf-8 -*-
"""
Created on Tue Oct 7 11:41:42 2018

@author: Caihao.Cui
https://github.com/cuicaihao/Webcam_QR_Detector/blob/master/Lab_02_Webcam_QR_Test.py
"""
from __future__ import print_function

import pyzbar.pyzbar as pyzbar
import numpy as np
import cv2
import time

def decode(im) : 
        decodedObjects = pyzbar.decode(im)
        return decodedObjects


def scanQRCode():
        cap = cv2.VideoCapture(0)

        cap.set(3,640)
        cap.set(4,480)
        time.sleep(2)

        font = cv2.FONT_HERSHEY_SIMPLEX

        while(cap.isOpened()):
                # Capture frame-by-frame
                ret, frame = cap.read()
                # Our operations on the frame come here
                im = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                 
                decodedObjects = decode(im)

                #    for decodedObject in decodedObjects: 
                if decodedObjects:
                        points = decodedObjects[0].polygon

                        # If the points do not form a quad, find convex hull
                        if len(points) > 4 : 
                                hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                                hull = list(map(tuple, np.squeeze(hull)))
                        else : 
                                hull = points;
                         
                        # Number of points in the convex hull
                        n = len(hull)     
                        # Draw the convext hull
                        for j in range(0,n):
                                cv2.line(frame, hull[j], hull[ (j+1) % n], (255,0,0), 3)

                        x = decodedObjects[0].rect.left
                        y = decodedObjects[0].rect.top

                        barcode = decodedObjects[0].data.decode('utf-8')
                        print('barcode = %s' % barcode)
                        break
 
                # Display the resulting frame
                cv2.imshow('frame',frame)
                key = cv2.waitKey(1)
                if key & 0xFF == ord('q'):
                        break
                elif key & 0xFF == ord('s'): # wait for 's' key to save 
                        cv2.imwrite('Capture.png', frame)     

        # When everything done, release the capture
        cap.release()
        cv2.destroyAllWindows()
        return barcode
