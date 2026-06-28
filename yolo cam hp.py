from ultralytics import YOLO

model = YOLO("model SmartMoney V2.onnx")

model.predict(
    source="http://192.168.101.7:8080/video",
    show=True,
    conf=0.5,
    device=0
)