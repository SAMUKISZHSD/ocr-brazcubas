# scripts/preprocess.py
import cv2
import os
from utils import load_config, ensure_dir_exists

# Carregar configurações
config = load_config()
input_dir = config["paths"]["input_dir"]
processed_dir = config["paths"]["processed_dir"]
threshold = config["ocr"]["threshold"]

# Garantir que o diretório de saída exista
ensure_dir_exists(processed_dir)

# Processar todas as imagens na pasta de entrada
for filename in os.listdir(input_dir):
    if filename.endswith('.jpg') or filename.endswith('.jpeg'):
        # Carregar a imagem
        image = cv2.imread(os.path.join(input_dir, filename))
        
        # Converter para escala de cinza
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Aplicar limiarização
        _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
        
        # Salvar a imagem processada
        output_path = os.path.join(processed_dir, filename)
        cv2.imwrite(output_path, binary)
        print(f"Imagem processada salva em: {output_path}")