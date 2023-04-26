from flask import Flask, render_template, Response, request, url_for, flash, redirect
import mysql.connector
import subprocess as sp
import sys
import cv2
import numpy as np
import random
import imutils
import time
import math
import os
from datetime import datetime
from sql import InsertRecords
from sql import SelectRecords

app = Flask(__name__ ,template_folder='./templates')

bounding_boxes = []

SelectedBox = None
prev_point = None
index = None
flag = None

camera = cv2.VideoCapture(0) 

cnx = mysql.connector.connect(user='root',database='turtle')

cursor = cnx.cursor()

cursor.execute("TRUNCATE  colour_changes ")

cursor.close()

cnx.close()



def detect_colour_change(frame,bbox):  # generate frame by frame from camera

    red_lower = np.array([170,150,50], np.uint8)
    red_upper = np.array([180,255,255], np.uint8)

    green_lower = np.array([55, 150, 50], np.uint8)
    green_upper = np.array([70, 255,255], np.uint8)

    yellow_lower = np.array([20, 150, 50], np.uint8)
    yellow_upper = np.array([35, 255, 255], np.uint8)

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

def select_bounding_boxes(File_name):

  global bounding_boxes
  
  if camera.isOpened:
    # Read first frame from camera feed
    success, frame = camera.read()
    # Quit if unable to read the video file
    frame = cv2.resize(frame,(1000 ,550))
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

    if(bbox != (0,0,0,0)):
      bounding_boxes.append(bbox)

    print("Press q to quit selecting boxes and start tracking")
    print("Press any other key to select next object")

    key = cv2.waitKey(0) & 0xff

    if (key == 113 and bounding_boxes):  # q is pressed
      cv2.destroyAllWindows()
      break
    else:
      print("\n You have not selected any bounding boxes !\n")

  f = open('bounding_boxes/' + File_name, 'w')
  for bbox in bounding_boxes:
      print(bbox)
      f.write(','.join(str(box) for box in bbox)+ '\n')

  print('Selected bounding boxes {}'.format(bounding_boxes))

def move_bounding_box(event, x, y, flags, File_name):

  global bounding_boxes

  global SelectedBox, prev_point, index

  if(event == cv2.EVENT_LBUTTONDOWN):
    for bbox in bounding_boxes:
        if (x >= bbox[0] and x <= (bbox[0]+bbox[2]) and y >= bbox[1] and y <= (bbox[1]+bbox[3])):
              SelectedBox = bbox
              index = bounding_boxes.index(bbox)
              prev_point = (x , y, bbox[0] + bbox[2], bbox[1] + bbox[3])

  elif event == cv2.EVENT_MOUSEMOVE:
    if SelectedBox is not None:
      dx = x - prev_point[0]
      dy = y - prev_point[1]
      SelectedBox = (SelectedBox[0] + dx , SelectedBox[1] + dy, SelectedBox[2], SelectedBox[3])
      if(SelectedBox[0] > 0 and SelectedBox[1] > 0 and SelectedBox[0] <= 843 and  SelectedBox[1] <= 433):
        prev_point = (x,y,SelectedBox[0] + dx + SelectedBox[2],SelectedBox[0] + dx + SelectedBox[2])
        bounding_boxes[index] = SelectedBox

  elif event == cv2.EVENT_LBUTTONUP:
    if SelectedBox is not None:
      f = open('bounding_boxes/' + File_name, 'w')
      for bbox in bounding_boxes:
        f.write(','.join(str(box) for box in bbox)+ '\n')
      f.close()
      SelectedBox = None

def write_to_file():

  choice = -1

  types = int, int, int, int

  global flag, bounding_boxes

  bounding_boxes.clear()

  entries = os.listdir('bounding_boxes/')

  File_name = None

  if entries and flag is None:
    for entry in entries:
      print(" [ " + str(entries.index(entry))  + " ] " + entry)
      flag = 1
    print(" [ " + str(len(entries))  + " ] " + "Make a new file")

  else:
    print("You have no bounding boxes data saved !")
  
  if flag is not None:
    while(choice > len(entries) or choice < 0 ):
      choice = int(input("Select one file: "))
      if(choice == len(entries)):
        flag = None
        break
      File_name = entries[choice]

    if flag == 1:
      with open ('bounding_boxes/' + entries[choice]) as inputfile:
        bounding_boxes = ([tuple(t(e) for t,e in zip(types, line.split(','))) for line in inputfile])

  if(flag is None):
    while(flag is None):
      input_name = input("Enter Bounding Box Data file name : ")
      File_name = input_name + '.txt'
      print(File_name)
      path = ('bounding_boxes/' + File_name)
      check_file = os.path.isfile(path)
      if check_file == False:
        select_bounding_boxes(File_name)
        f = open('bounding_boxes/' + File_name, 'w')
        for bbox in bounding_boxes:
            print(bbox)
            f.write(','.join(str(box) for box in bbox)+ '\n')
        f.close()
        flag = 1
      else:
        print("The File Already Exists\n")
  
  return File_name


def gen_frames():

  global flag, bounding_boxes
  
  time.sleep(1.5)

  if(flag == None):

    File_name = write_to_file()
  
  while True:

    success, frame = camera.read()
    
    frame = cv2.resize(frame,(1000 ,550))

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
    cv2.setMouseCallback('VideoStream', move_bounding_box, File_name)
    cv2.imshow('VideoStream', frame) 

    ret , buffer = cv2.imencode('.jpg', frame)
    frame = buffer.tobytes()
    yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
            
    # Select More Bounding Boxes
    if cv2.waitKey(1) & 0xFF == ord('v'):  # v Pressed
      select_bounding_boxes(File_name)

    # Choose a different file
    if cv2.waitKey(1) & 0xFF == ord('m'):  # m Pressed
      flag = None
      File_name = write_to_file()
  
    # Quit on ESC button
    if cv2.waitKey(1) & 0xFF == 27:  # Esc pressed
      break

@app.route('/', methods=["GET","POST"])
def index():
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

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True) 