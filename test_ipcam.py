import cv2

url = "http://192.168.101.7:8080/video"

cap = cv2.VideoCapture(url)

while True:
    ret, frame = cap.read()

    if not ret:
        print("Gagal membaca stream")
        break

    cv2.imshow("IP Webcam", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()