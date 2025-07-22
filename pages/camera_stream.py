import streamlit as st
import cv2
import torch
import numpy as np
from ultralytics import YOLO
import time
from PIL import Image
from mqtt import MosquittoLocalClient

cliente = MosquittoLocalClient("python_client")
if not cliente.connect():
    exit("Não foi possível conectar ao Mosquitto local. Verifique se o broker está rodando.")
# Configurações
MODEL_NAME = 'yolov8n.pt'
BIRD_CLASS_ID = 14
CONFIDENCE_THRESHOLD = 0.2
NMS_THRESHOLD = 0.45
WEBCAM_ID = 0
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720

# Título da aplicação
st.title("Sistema de Detecção de Pombos em Tempo Real")

# Sidebar para configurações
st.sidebar.header("Configurações")
confidence_threshold = st.sidebar.slider("Limiar de Confiança", 0.1, 0.9, CONFIDENCE_THRESHOLD, 0.05)
show_fps = st.sidebar.checkbox("Mostrar FPS", value=True)
show_detection_count = st.sidebar.checkbox("Mostrar Contagem de Detecções", value=True)

# Carregar o modelo YOLO
@st.cache_resource
def load_model():
    return YOLO(MODEL_NAME)

model = load_model()

# Funções de detecção (mantidas do seu código original)
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
    
    info_texts = []
    if show_fps:
        info_texts.append(f"FPS: {fps:.1f}")
    info_texts.append(f"Status: {'SIM' if has_pigeon else 'NAO'}")
    info_texts.append(f"Confiança: {confidence_threshold:.1f}")
    if show_detection_count:
        info_texts.append(f"Detecções: {len(detections)}")
    
    info_height = len(info_texts) * 22 + 20
    cv2.rectangle(frame_copy, (10, 10), (250, info_height), (0, 0, 0), -1)
    cv2.rectangle(frame_copy, (10, 10), (250, info_height), (255, 255, 255), 1)
    
    for i, text in enumerate(info_texts):
        y_pos = 30 + i * 22
        if "Status:" in text:
            color = (0, 255, 0) if has_pigeon else (0, 0, 255)
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

# Inicializar a captura de vídeo
cap = cv2.VideoCapture(WEBCAM_ID)
if not cap.isOpened():
    st.error("Não foi possível abrir a webcam. Verifique se a câmera está conectada.")
    st.stop()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, DISPLAY_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DISPLAY_HEIGHT)

# Placeholder para a imagem
image_placeholder = st.empty()

# Controles de execução
start_button = st.button("Iniciar Detecção")
stop_button = st.button("Parar Detecção")

# Variáveis de estado
if 'running' not in st.session_state:
    st.session_state.running = False

if start_button:
    st.session_state.running = True

if stop_button:
    st.session_state.running = False
    cap.release()

# Loop principal de detecção
fps_counter = 0
fps_timer = time.time()
frames_with_pigeon = 0
frames_without_pigeon = 0

while st.session_state.running:
    ret, frame = cap.read()
    if not ret:
        st.error("Erro ao capturar frame da webcam.")
        st.session_state.running = False
        break
    
    # Detectar pombos
    detections = detect_pigeons_in_frame(frame, model, confidence_threshold)
    has_pigeon = len(detections) > 0
    
    # Atualizar contadores
    if has_pigeon:
        cliente.publicar(f"ativos/EMAP", "True")
        frames_with_pigeon += 1
    else:
        cliente.publicar(f"ativos/EMAP", "False")
        frames_without_pigeon += 1
    
    # Calcular FPS
    fps_counter += 1
    if time.time() - fps_timer > 1.0:
        fps = fps_counter / (time.time() - fps_timer)
        fps_counter = 0
        fps_timer = time.time()
    else:
        fps = fps_counter / max(time.time() - fps_timer, 0.01)
    
    # Desenhar detecções
    frame_with_detections = draw_detections(frame, detections, fps if show_fps else 0)
    
    # Converter de BGR para RGB
    frame_rgb = cv2.cvtColor(frame_with_detections, cv2.COLOR_BGR2RGB)
    
    # Exibir frame no Streamlit
    image_placeholder.image(frame_rgb, channels="RGB")
    
    # Pequena pausa para evitar sobrecarga
    time.sleep(0.01)

# Estatísticas finais
if frames_with_pigeon + frames_without_pigeon > 0:
    st.subheader("Estatísticas de Detecção")
    col1, col2 = st.columns(2)
    col1.metric("Frames com Pombos", frames_with_pigeon)
    col2.metric("Frames sem Pombos", frames_without_pigeon)
    st.metric("Taxa de Detecção", f"{(frames_with_pigeon / (frames_with_pigeon + frames_without_pigeon)) * 100:.1f}%")

# Limpeza
if cap.isOpened():
    cap.release()