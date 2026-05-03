# convert model:
```yolo export model=Base_station/models/train/weights/best.pt format=edgetpu imgsz=800 data=Base_station/dataset/dataset.yaml```

# Creating own dataset

### CARLA

### FineTuned on manual labeled images

points:
1. left bottom back
2. left top back
3. right bottom back
4. right top back
5. left bottom front 
6. left top front
7. right bottom front 
8. right top front

