# scripts/ocr.py
import easyocr
import os
import cv2
import numpy as np
from utils import load_config, ensure_dir_exists
from concurrent.futures import ThreadPoolExecutor
import torch

# Carregar configurações
config = load_config()
processed_dir = config["paths"]["processed_dir"]
text_dir = config["paths"]["text_dir"]
language = config["ocr"]["language"]

# Garantir que o diretório de saída exista
ensure_dir_exists(text_dir)

# Inicializar o EasyOCR com configurações otimizadas
reader = easyocr.Reader(
    ['pt'],
    gpu=torch.cuda.is_available(),  # Usa GPU se disponível
    model_storage_directory='./models',  # Cache local dos modelos
    download_enabled=True
)

def preprocess_image(image):
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

def process_single_image(filename):
    if not (filename.endswith('.jpg') or filename.endswith('.jpeg')):
        return
    
    # Caminho da imagem processada
    image_path = os.path.join(processed_dir, filename)
    
    # Ler e pré-processar a imagem
    image = cv2.imread(image_path)
    processed_image = preprocess_image(image)
    
    # Extrair texto usando EasyOCR com configurações otimizadas
    results = reader.readtext(
        processed_image,
        batch_size=4,  # Processa múltiplas regiões simultaneamente
        paragraph=True,  # Agrupa texto em parágrafos
        detail=0  # Retorna apenas o texto
    )
    
    # Juntar resultados
    text = '\n'.join(results)
    
    # Limpar e formatar o texto
    text = text.replace('\n\n', '\n')
    text = ' '.join(text.split())
    
    # Salvar o texto extraído
    output_path = os.path.join(text_dir, filename.replace('.jpg', '.txt'))
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Texto extraído salvo em: {output_path}")

# Processar imagens em paralelo
def process_images():
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(process_single_image, os.listdir(processed_dir))

if __name__ == "__main__":
    process_images()