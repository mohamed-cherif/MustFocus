import sys
import os
import argparse
import time
import datetime
import cv2
import numpy as np
import pyautogui
import matplotlib.pyplot as plt

from gaze_tracker import GazeTracker
from calibration import calibrate
from screen import Screen

focus = []

RES_SCREEN = pyautogui.size()

SCREEN_WIDTH = 1520
SCREEN_HEIGHT = 880

FRAME_WIDTH = 640
FRAME_HEIGHT = 480

def nothing(val):
    pass

def main():
    lost = 0
    # remote source
    camera = cv2.VideoCapture(0)

    # webcam source
#    camera = cv2.VideoCapture(0)
#    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
#    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    gaze_tracker = GazeTracker()
    screen = Screen(SCREEN_WIDTH, SCREEN_HEIGHT)

    cv2.namedWindow("frame")
    cv2.createTrackbar('threshold', 'frame', 0, 255, nothing)
    cv2.setTrackbarPos('threshold', 'frame', 1)

    screen.clean()
    screen.show()

    os.makedirs('images', exist_ok=True)

    while True:
        _, frame = camera.read() 

#        print(frame.shape)

        start = time.time()

        gaze_tracker.update(frame)

        end = time.time()

        cv2.namedWindow("frame")
        dec_frame = gaze_tracker.eye_tracker.decorate_frame()
        

        dec_frame = cv2.resize(dec_frame,(int(FRAME_WIDTH / 2), int(FRAME_HEIGHT / 2)))
        dec_frame[np.where((dec_frame==[255,255,255]).all(axis=2))] = [0,0,0]
        cv2.moveWindow("frame", 0 , 0)
        cv2.imshow('frame', dec_frame)

        try:
            gaze = gaze_tracker.get_gaze()
            focus.append(gaze)
        except:
            gaze = None
            screen.print_message("CALIBRATION REQUIRED!")
            screen.show()
            print("CALIBRATION REQUIRED!")

        print("GAZE: {}".format(gaze))

        if gaze:
            screen.update(gaze)
            screen.refresh()
            if gaze[1]<526:
                lost = lost + 1
            try:
                pyautogui.moveTo(gaze[0] + ((RES_SCREEN[0] - screen.width) // 2), gaze[1] + 25)
            except:
                pass

        print("TIME: {:.3f} ms".format(end*1000 - start*1000))
        time.sleep(0.1)

        k = cv2.waitKey(1) & 0xff
        if k == 1048603 or k == 27: # esc to quit
            break
        if k == ord('c'): # c to calibrate
            screen.mode = "calibration"
            screen.draw_center()
            calibrate(camera, screen, gaze_tracker)

    camera.release()
    cv2.destroyAllWindows()
    focus_x = [d for d in focus if d is not None]
    plt.xlim(right=1920)
    plt.ylim(top=1080)
    plt.xlabel('width')
    plt.ylabel('height')
    plt.title('Focus points')
    plt.scatter(*zip(*focus_x))
    plt.show()
    plt.hexbin(*zip(*focus_x), cmap='YlOrRd', alpha=0.8)
    plt.show()
    plost = (lost*100)/len(focus)
    pfound = 100-plost
    print("Lost: ", plost, "%")
    print("Focused: ", pfound, "%")


if __name__ == '__main__':
    main()
