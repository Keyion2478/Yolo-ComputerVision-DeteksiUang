import cv2
import time
from ultralytics import YOLO

# ==========================================================
# LOAD MODEL
# ==========================================================

model = YOLO("model SmartMoney V4.pt")


# ==========================================
# CAMERA CONFIG
# ==========================================

USE_PHONE_CAMERA = True

PHONE_IP = "192.168.1.39"
PHONE_PORT = 8080

if USE_PHONE_CAMERA:

    STREAM_URL = f"http://{PHONE_IP}:{PHONE_PORT}/video"
    cap = cv2.VideoCapture(STREAM_URL)

else:

    cap = cv2.VideoCapture(0)

# ==========================================================
# KONFIGURASI
# ==========================================================

CONF_THRESHOLD = 0.80          # Confidence minimal YOLO
MIN_STABLE_CONF = 85.0         # Confidence minimal agar timer tetap jalan
STABLE_TIME = 2.0              # Harus stabil selama 2 detik
GRACE_TIME = 0.5               # Objek hilang maksimal 0.5 detik

# Maksimal perubahan bounding box
CENTER_TOLERANCE = 40          # pixel
SIZE_TOLERANCE = 0.20          # 20%

# ==========================================================
# VARIABEL
# ==========================================================

last_class = None
start_time = None
data_sent = False

object_missing_time = None

last_box = None

print("=" * 50)
print("SMART MONEY DETECTION STARTED")
print("=" * 50)

while True:

    ret, frame = cap.read()

    if not ret:
        break

    results = model(
        frame,
        conf=CONF_THRESHOLD,
        verbose=False
    )

    # ======================================================
    # ADA OBJEK
    # ======================================================

    if len(results[0].boxes) > 0:

        object_missing_time = None

        # Ambil confidence tertinggi
        box = max(
            results[0].boxes,
            key=lambda b: float(b.conf)
        )

        class_id = int(box.cls[0])
        class_name = model.names[class_id]
        confidence = float(box.conf[0]) * 100

        x1, y1, x2, y2 = box.xyxy[0].tolist()

        width = x2 - x1
        height = y2 - y1

        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        current_box = {
            "cx": center_x,
            "cy": center_y,
            "w": width,
            "h": height
        }

        # ==================================================
        # DETEKSI BARU
        # ==================================================

        if class_name != last_class:

            last_class = class_name
            last_box = current_box

            start_time = time.time()

            data_sent = False

            print("\n" + "=" * 50)
            print("DETEKSI BARU")
            print("Nominal    :", class_name)
            print("Confidence :", round(confidence, 2), "%")
            print("=" * 50)

        # ==================================================
        # DETEKSI MASIH SAMA
        # ==================================================

        else:

            stable = True

            # ------------------------------
            # Confidence Stabil
            # ------------------------------

            if confidence < MIN_STABLE_CONF:

                stable = False

            # ------------------------------
            # Bounding Box Stabil
            # ------------------------------

            dx = abs(current_box["cx"] - last_box["cx"])
            dy = abs(current_box["cy"] - last_box["cy"])

            dw = abs(current_box["w"] - last_box["w"]) / last_box["w"]
            dh = abs(current_box["h"] - last_box["h"]) / last_box["h"]

            if dx > CENTER_TOLERANCE:
                stable = False

            if dy > CENTER_TOLERANCE:
                stable = False

            if dw > SIZE_TOLERANCE:
                stable = False

            if dh > SIZE_TOLERANCE:
                stable = False

            # ------------------------------
            # Timer
            # ------------------------------

            if not stable:

                start_time = time.time()

                last_box = current_box

                print("\rMenunggu objek stabil...", end="")

            else:

                elapsed = time.time() - start_time

                print(
                    f"\rStabil : {elapsed:.1f}/{STABLE_TIME} detik",
                    end=""
                )

                if elapsed >= STABLE_TIME and not data_sent:

                    print("\n")

                    print("=" * 50)
                    print("DETEKSI STABIL")
                    print("Class ID   :", class_id)
                    print("Nominal    :", class_name)
                    print("Confidence :", round(confidence,2), "%")
                    print("=" * 50)

                    ###################################################
                    # FIREBASE AKAN DITAMBAHKAN DI SINI
                    ###################################################

                    data_sent = True

        last_box = current_box

    # ======================================================
    # TIDAK ADA OBJEK
    # ======================================================

    else:

        if object_missing_time is None:

            object_missing_time = time.time()

        else:

            missing = time.time() - object_missing_time

            if missing >= GRACE_TIME:

                if last_class is not None:

                    print("\n")
                    print("=" * 50)
                    print("OBJEK KELUAR")
                    print("Sistem siap mendeteksi uang berikutnya.")
                    print("=" * 50)

                last_class = None
                last_box = None
                start_time = None
                data_sent = False
                object_missing_time = None

    # ======================================================
    # TAMPILKAN FRAME
    # ======================================================

    annotated = results[0].plot()

    cv2.imshow("Smart Money Detection", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()