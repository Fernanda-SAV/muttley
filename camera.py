import cv2
import torch
import numpy as np
from ultralytics import YOLO
import time

MODEL_NAME = 'yolov8n.pt'
BIRD_CLASS_ID = 14
CONFIDENCE_THRESHOLD = 0.3
NMS_THRESHOLD = 0.45
WEBCAM_ID = 0
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720

model = YOLO(MODEL_NAME)

def detect_pigeons_in_frame(frame, model, conf_threshold=CONFIDENCE_THRESHOLD):
    results = model(frame, conf=conf_threshold, verbose=False)
    pigeon_detections = []
    
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for box in boxes:
                if int(box.cls) == BIRD_CLASS_ID:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    pigeon_detections.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': float(confidence),
                        'label': 'Pombo',
                        'class_id': 0
                    })
    return pigeon_detections

def draw_detections(frame, detections, fps=0):
    frame_copy = frame.copy()
    height, width = frame.shape[:2]
    has_pigeon = len(detections) > 0
    
    if has_pigeon:
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
            text = f"Pombo: {confidence:.2f}"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame_copy, (x1, y1 - text_size[1] - 10), 
                         (x1 + text_size[0] + 5, y1), (0, 255, 0), -1)
            cv2.putText(frame_copy, text, (x1 + 2, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    if has_pigeon:
        status_text = "POMBO DETECTADO!"
        status_color = (0, 255, 0)
        bg_color = (0, 150, 0)
    else:
        status_text = "NENHUM POMBO"
        status_color = (0, 0, 255)
        bg_color = (0, 0, 150)
    
    text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
    text_x = (width - text_size[0]) // 2
    text_y = 80
    
    cv2.rectangle(frame_copy, 
                  (text_x - 20, text_y - text_size[1] - 20),
                  (text_x + text_size[0] + 20, text_y + 10),
                  bg_color, -1)
    cv2.rectangle(frame_copy, 
                  (text_x - 20, text_y - text_size[1] - 20),
                  (text_x + text_size[0] + 20, text_y + 10),
                  status_color, 3)
    cv2.putText(frame_copy, status_text, (text_x, text_y), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.5, status_color, 3)
    
    info_texts = [
        f"FPS: {fps:.1f}",
        f"Status: {'SIM' if has_pigeon else 'NAO'}",
        f"Confianca: {CONFIDENCE_THRESHOLD:.1f}",
        f"Deteccoes: {len(detections)}",
        "",
        "Controles:",
        "ESC/Q - Sair",
        "+ - Mais sensivel",
        "- - Menos sensivel",
        "R - Reset"
    ]
    
    info_height = len(info_texts) * 22 + 20
    cv2.rectangle(frame_copy, (10, 10), (250, info_height), (0, 0, 0), -1)
    cv2.rectangle(frame_copy, (10, 10), (250, info_height), (255, 255, 255), 1)
    
    for i, text in enumerate(info_texts):
        if text == "":
            continue
        y_pos = 30 + i * 22
        if "Status:" in text:
            color = (0, 255, 0) if has_pigeon else (0, 0, 255)
        elif "Controles:" in text:
            color = (255, 255, 0)
        elif text.startswith(("ESC", "+", "-", "R")):
            color = (200, 200, 200)
        else:
            color = (255, 255, 255)
        cv2.putText(frame_copy, text, (15, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
    
    circle_color = (0, 255, 0) if has_pigeon else (0, 0, 255)
    circle_center = (width - 50, 50)
    cv2.circle(frame_copy, circle_center, 30, circle_color, -1)
    cv2.circle(frame_copy, circle_center, 30, (255, 255, 255), 2)
    circle_text = "✓" if has_pigeon else "✗"
    cv2.putText(frame_copy, circle_text, (width - 62, 60), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    
    return frame_copy

def run_realtime_pigeon_detection():
    cap = cv2.VideoCapture(WEBCAM_ID)
    if not cap.isOpened():
        return False
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, DISPLAY_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DISPLAY_HEIGHT)
    
    frame_count = 0
    fps_counter = 0
    fps_timer = time.time()
    frames_with_pigeon = 0
    frames_without_pigeon = 0
    current_confidence = CONFIDENCE_THRESHOLD
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            detections = detect_pigeons_in_frame(frame, model, current_confidence)
            has_pigeon = len(detections) > 0
            
            if has_pigeon:
                frames_with_pigeon += 1
            else:
                frames_without_pigeon += 1
            
            fps_counter += 1
            if time.time() - fps_timer > 1.0:
                fps = fps_counter / (time.time() - fps_timer)
                fps_counter = 0
                fps_timer = time.time()
            else:
                fps = fps_counter / max(time.time() - fps_timer, 0.01)
            
            frame_with_detections = draw_detections(frame, detections, fps)
            cv2.imshow('Deteccao de Pombos', frame_with_detections)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q'):
                break
            elif key == ord('+') or key == ord('='):
                current_confidence = max(0.1, current_confidence - 0.1)
            elif key == ord('-'):
                current_confidence = min(0.9, current_confidence + 0.1)
            elif key == ord('r'):
                current_confidence = CONFIDENCE_THRESHOLD
            
            frame_count += 1
    
    except KeyboardInterrupt:
        pass
    except Exception as e:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
        return True

def test_webcam():
    cap = cv2.VideoCapture(WEBCAM_ID)
    if not cap.isOpened():
        for i in range(1, 4):
            test_cap = cv2.VideoCapture(i)
            if test_cap.isOpened():
                test_cap.release()
                return i
            test_cap.release()
        return None
    
    ret, frame = cap.read()
    if ret:
        cap.release()
        return WEBCAM_ID
    else:
        cap.release()
        return None

def configure_detection():
    global CONFIDENCE_THRESHOLD, WEBCAM_ID, MODEL_NAME
    working_webcam = test_webcam()
    if working_webcam is not None and working_webcam != WEBCAM_ID:
        WEBCAM_ID = working_webcam
    return working_webcam is not None

def main():
    if not configure_detection():
        return False
    return run_realtime_pigeon_detection()

if __name__ == "__main__":
    main()