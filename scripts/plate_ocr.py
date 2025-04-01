import easyocr
import cv2
import numpy as np
import torch
import re
from utils import load_config

# Carregar configurações
config = load_config()
language = config["ocr"]["language"]

# Inicializar o EasyOCR com configurações otimizadas para placas
reader = easyocr.Reader(
    ['pt'],
    gpu=torch.cuda.is_available(),
    model_storage_directory='./models',
    download_enabled=True
)

def preprocess_plate_image(image):
    """Pré-processa a imagem para melhor reconhecimento de placas"""
    # Converter para escala de cinza
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Aumentar resolução da imagem
    scale = 2
    enlarged = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Reduzir ruído preservando bordas
    denoised = cv2.fastNlMeansDenoising(enlarged, None, 10, 7, 21)
    
    # Melhorar nitidez
    kernel = np.array([[-1,-1,-1],
                      [-1, 9,-1],
                      [-1,-1,-1]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    
    # Melhorar contraste adaptativo
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(sharpened)
    
    # Ajustar brilho e contraste
    alpha = 1.2  # Contraste
    beta = 10    # Brilho
    adjusted = cv2.convertScaleAbs(enhanced, alpha=alpha, beta=beta)
    
    return adjusted

def is_valid_plate(text):
    """Verifica se o texto corresponde ao formato de placa brasileira"""
    # Padrão de placa brasileira (antiga ou Mercosul)
    plate_pattern = r'^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$|^[A-Z]{3}[0-9]{4}$'
    return bool(re.match(plate_pattern, text))

def process_plate(image):
    """Processa a imagem e retorna a placa encontrada"""
    try:
        # Pré-processar a imagem
        processed_image = preprocess_plate_image(image)
        
        # Extrair texto usando EasyOCR
        results = reader.readtext(
            processed_image,
            batch_size=4,
            paragraph=False,
            detail=1  # Retorna texto e confiança
        )
        
        # Filtrar e processar resultados
        valid_plates = []
        for (bbox, text, prob) in results:
            # Limpar o texto (remover espaços e converter para maiúsculas)
            text = ''.join(text.split()).upper()
            
            # Verificar se é uma placa válida
            if is_valid_plate(text):
                valid_plates.append({
                    'plate': text,
                    'confidence': prob
                })
        
        # Retornar a placa com maior confiança
        if valid_plates:
            best_plate = max(valid_plates, key=lambda x: x['confidence'])
            return {
                'success': True,
                'plate': best_plate['plate'],
                'confidence': best_plate['confidence']
            }
        
        return {
            'success': False,
            'error': 'Nenhuma placa válida encontrada na imagem'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Erro ao processar imagem: {str(e)}'
        } 