from flask import Flask, render_template, Response, request, url_for, flash, redirect, session, request
from flask_session import Session
from flask import jsonify
import subprocess as sp
import sys
import cv2
import numpy as np
import random
import imutils
import time
import os 
import math
import keyboard
from sql import InsertRecords
from sql import SelectRecords

app = Flask(__name__ ,template_folder='./templates')

bounding_boxes = []

SelectedBox = None
prev_point = None
index = None
session = None
red_lower = np.array([0, 100, 100])
red_upper = np.array([10, 255, 255])
yellow_lower = np.array([25, 100, 100])
yellow_upper = np.array([35, 255, 255])
green_lower = np.array([50, 100, 100])
green_upper = np.array([70, 255, 255])

camera = cv2.VideoCapture(0)

@app.route('/input_colour_values', methods=['POST'])
def input_colour_values():
    global red_lower, red_upper, yellow_lower, yellow_upper, green_lower, green_upper
    
    if request.method == 'POST':
        redlower_hue = request.form['redlower_hue']
        redlower_saturation = request.form['redlower_saturation']
        redlower_value = request.form['redlower_value']
    
        redupper_hue = request.form['redupper_hue']
        redupper_saturation = request.form['redupper_saturation']
        redupper_value = request.form['redupper_value']
    
        yellowlower_hue = request.form['yellowlower_hue']
        yellowlower_saturation = request.form['yellowlower_saturation']
        yellowlower_value = request.form['yellowlower_value']
    
        yellowupper_hue = request.form['yellowupper_hue']
        yellowupper_saturation = request.form['yellowupper_saturation']
        yellowupper_value = request.form['yellowupper_value']
    
        greenlower_hue = request.form['greenlower_hue']
        greenlower_saturation = request.form['greenlower_saturation']
        greenlower_value = request.form['greenlower_value']
    
        greenupper_hue = request.form['greenupper_hue']
        greenupper_saturation = request.form['greenupper_saturation']
        greenupper_value = request.form['greenupper_value']
    
        red_lower = np.array([int(redlower_hue), int(redlower_saturation), int(redlower_value)], np.uint8)
        red_upper = np.array([int(redupper_hue), int(redupper_saturation), int(redupper_value)], np.uint8)

        yellow_lower = np.array([int(yellowlower_hue), int(yellowlower_saturation), int(yellowlower_value)], np.uint8)
        yellow_upper = np.array([int(yellowupper_hue), int(yellowupper_saturation), int(yellowupper_value)], np.uint8)

        green_lower = np.array([int(greenlower_hue), int(greenlower_saturation), int(greenlower_value)], np.uint8)
        green_upper = np.array([int(greenupper_hue), int(greenupper_saturation), int(greenupper_value)], np.uint8)
    
    return render_template("index.html")
        
    
def detect_colour_change(frame,bbox):  # generate frame by frame from camera
    global red_lower, red_upper, yellow_lower, yellow_upper, green_lower, green_upper
    
    roicolor = frame[bbox[1]:bbox[1]+bbox[3],(bbox[0]):(bbox[0]+bbox[2])]
    
    hsvFrame = cv2.cvtColor(roicolor, cv2.COLOR_BGR2HSV)

    #Red Mask
    red_mask = cv2.inRange(hsvFrame, red_lower, red_upper)

    #Green Mask
    green_mask = cv2.inRange(hsvFrame, green_lower, green_upper)

    #Green Mask
    yellow_mask = cv2.inRange(hsvFrame, yellow_lower, yellow_upper)

    # Morphological Transform, Dilation
    # for each color and bitwise_and operator
    # between imageFrame and mask determines
    # to detect only that particular color
    kernel = np.ones((5, 5), "uint8")
    
    # For red color
    red_mask = cv2.dilate(red_mask, kernel)
    res_red = cv2.bitwise_and(roicolor, roicolor, mask = red_mask)
    
    # For green color
    green_mask = cv2.dilate(green_mask, kernel)
    res_green = cv2.bitwise_and(roicolor, roicolor,mask = green_mask)
    
    # For blue color
    yellow_mask = cv2.dilate(yellow_mask, kernel)
    res_yellow = cv2.bitwise_and(roicolor, roicolor,mask = yellow_mask)

    #Finding the Contours
    contours, hierarchy = cv2.findContours(red_mask + yellow_mask + green_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
      (x, y, w, h) = cv2.boundingRect(contour)
      
      #Red
      if(cv2.contourArea(contour) > 300):
        roi = hsvFrame[y:y+h, x:x+w]
        red_pixels = cv2.countNonZero(cv2.inRange(roi, red_lower, red_upper))
        if red_pixels > 0:
          return ('red', bounding_boxes.index(bbox))

      #Yellow
      if(cv2.contourArea(contour) > 300):
        roi = hsvFrame[y:y+h, x:x+w]
        yellow_pixels = cv2.countNonZero(cv2.inRange(roi, yellow_lower, yellow_upper))
        if yellow_pixels > 0:
          return ('yellow', bounding_boxes.index(bbox))

      #Green        
      if(cv2.contourArea(contour) > 300):
        roi = hsvFrame[y:y+h, x:x+w]
        green_pixels = cv2.countNonZero(cv2.inRange(roi, green_lower, green_upper))
        if green_pixels > 0:
          return ('green', bounding_boxes.index(bbox))

      return None

def select_bounding_boxes():
  
  if camera.isOpened:
    # Read first frame from camera feed
    success, frame = camera.read()
    # Quit if unable to read the video file
    frame = cv2.resize(frame,(1000 ,600))
    if not success:
      print('Failed to read video')
      sys.exit(1)
      
  else: 
    print("Cannot Open Camera")
    
  while True:
    # draw bounding boxes over objects
    # selectROI's default behaviour is to draw box starting from the center
    # when fromCenter is set to false, you can draw box starting from top left corner
    bbox = cv2.selectROI('MultiTracker', frame)
    bounding_boxes.append(bbox)

    print("Press q to quit selecting boxes and start tracking")
    print("Press any other key to select next object")

    key = cv2.waitKey(0) & 0xff

    if (key == 113 and bounding_boxes):  # q is pressed
      cv2.destroyAllWindows()
      break
    else:
      print("You have not selected any bounding boxes !")

  print('Selected bounding boxes {}'.format(bounding_boxes))

def move_bounding_box(event, x, y, flags, param):
  
  global SelectedBox, prev_point, index

  if(event == cv2.EVENT_LBUTTONDOWN):
    for bbox in bounding_boxes:
        if (x >= bbox[0] and x <= (bbox[0]+bbox[2]) and y >= bbox[1] and y <= (bbox[1]+bbox[3])):
              SelectedBox = bbox
              index = bounding_boxes.index(bbox)
              prev_point = (x,y)

  elif event == cv2.EVENT_MOUSEMOVE:
    if SelectedBox is not None:
      dx = x - prev_point[0]
      dy = y - prev_point[1]
      SelectedBox = (SelectedBox[0] + dx , SelectedBox[1] + dy, SelectedBox[2], SelectedBox[3])
      prev_point = (x, y)
      if(SelectedBox[0] > 0 and SelectedBox[1] > 0 and (SelectedBox[0]+SelectedBox[2]) > 0 and (SelectedBox[1] + SelectedBox[3]) > 0):
        bounding_boxes[index] = SelectedBox

  elif event == cv2.EVENT_LBUTTONUP:
    if SelectedBox is not None:
        bounding_boxes[index] = SelectedBox
        SelectedBox = None

def gen_frames():
  
  global session

  if(session is None):

    select_bounding_boxes()
    session = 1
  
  while True:

    success, frame = camera.read()
    
    frame = cv2.resize(frame,(1000 ,600))

    if not success:
      break
    
    for bbox in bounding_boxes:
      cv2.rectangle (frame,(bbox[0],bbox[1]),((bbox[0]+bbox[2]),(bbox[1]+bbox[3])), (255,255,255), 3)
      x = math.floor((bbox[0] + bbox[0] + bbox[2])/2)
      cv2.putText(frame,str(bounding_boxes.index(bbox)), (x,bbox[1]), cv2.FONT_HERSHEY_SIMPLEX, 1.0,(0,0,255),2)
      colour_changes = detect_colour_change(frame, bbox)

      if (colour_changes is not None):
          current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
          InsertRecords(colour_changes[1], colour_changes[0], current_time)

    cv2.namedWindow('VideoStream')
    cv2.setMouseCallback('VideoStream', move_bounding_box)
    cv2.imshow('VideoStream', frame) 

    ret , buffer = cv2.imencode('.jpg', frame)
    frame = buffer.tobytes()
    yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
            
    # Select More Bounding Boxes
    if cv2.waitKey(1) & 0xFF == ord('v'):  # v Pressed
      select_bounding_boxes()
  
    # Quit on ESC button
    if cv2.waitKey(1) & 0xFF == 27:  # Esc pressed
      break

  cv2.destroyAllWindows()
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/', methods=["GET","POST"])
def index():
  '''
    start = None
    stop = None
    if(request.method == 'POST'):
      start = request.form['Start']
      stop = request.form['Stop']

    if(stop == 'stop'):
        print('shutdown')
        return redirect("/shutdown",code = 302)
  '''
  return render_template('index.html')

@app.route('/stream')
def stream():
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/updates', methods=["GET", "POST"])
def updates():
    flag = True
    if request.method == 'POST':

      search_query = request.form['search_query']
      search_column = request.form['search_column']
      result = SelectRecords(search_query,search_column)

      if(search_column == 'bounding_box_id'):
        try:
          int(search_query)
        
        except ValueError:
          flag = False
      
        if flag == False:
          result = []
    else:

      result  = []
    

    return render_template('updates.html', results = result)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True) 