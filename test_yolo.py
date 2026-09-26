from ultralytics import YOLO

model = YOLO("yolov8n.pt")   # nano version (small model)

results = model("test2.jpg")  # use your test image

for r in results:
    for box in r.boxes:
        cls = int(box.cls[0])
        print(model.names[cls])