import cv2
import os
import urllib.request
import numpy as np

# Download YOLOv3 files if they don't exist
cfg_path = 'yolov3.cfg'
weights_path = 'yolov3.weights'
names_path = 'coco.names'

opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')]
urllib.request.install_opener(opener)

if not os.path.exists(cfg_path):
    print("Downloading YOLOv3 config...")
    urllib.request.urlretrieve('https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov3.cfg', cfg_path)
    
if not os.path.exists(weights_path):
    print("Downloading YOLOv3 weights...")
    urllib.request.urlretrieve('https://pjreddie.com/media/files/yolov3.weights', weights_path)

if not os.path.exists(names_path):
    print("Downloading COCO names...")
    urllib.request.urlretrieve('https://raw.githubusercontent.com/AlexeyAB/darknet/master/data/coco.names', names_path)

# Load classes
with open(names_path, "r") as f:
    CLASSES = [line.strip() for line in f.readlines()]

# Load network
net = cv2.dnn.readNetFromDarknet(cfg_path, weights_path)
output_layers = net.getUnconnectedOutLayersNames()

# Classes we consider as "herd" animals in COCO dataset
ANIMAL_CLASSES = ["bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"]

def get_yolo_detections(image):
    (h, w) = image.shape[:2]
    # Optimal input resolution for full YOLOv3
    blob = cv2.dnn.blobFromImage(image, 1/255.0, (608, 608), swapRB=True, crop=False)
    net.setInput(blob)
    outputs = net.forward(output_layers)

    boxes = []
    confidences = []
    class_ids = []

    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            # Filter out weak detections (using a lower threshold for distant herds)
            if confidence > 0.08:  # Lowered from 0.15 for better recall on small sheep
                label = CLASSES[class_id]
                if label in ANIMAL_CLASSES:
                    box = detection[0:4] * np.array([w, h, w, h])
                    (centerX, centerY, width, height) = box.astype("int")
                    
                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))
                    
                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

    # Apply Non-Max Suppression to remove overlapping boxes (adjusted threshold)
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, 0.08, 0.4)
    
    animal_count = 0
    if len(idxs) > 0:
        for i in idxs.flatten():
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])
            
            # Draw bounding box
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw label
            label = f"{CLASSES[class_ids[i]]}: {confidences[i]*100:.1f}%"
            y_offset = y - 10 if y - 10 > 10 else y + 10
            cv2.putText(image, label, (x, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
            animal_count += 1
            
    return animal_count, image

def detect_animals_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return 0, False
        
    animal_count, processed_image = get_yolo_detections(image)
    
    output_path = 'static/output.jpg'
    cv2.imwrite(output_path, processed_image)
    
    alert = animal_count >= 3
    return animal_count, alert

def detect_animals_video(video_path):
    cap = cv2.VideoCapture(video_path)
    output_video = 'static/output_video.avi'
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_video, fourcc, 20.0, (width, height))
    
    max_animals = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        animal_count, processed_frame = get_yolo_detections(frame)
        
        if animal_count > max_animals:
            max_animals = animal_count
            
        out.write(processed_frame)
        
    cap.release()
    out.release()
    
    alert = max_animals >= 3
    return max_animals, alert
