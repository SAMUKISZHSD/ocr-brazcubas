# scripts/postprocess.py
import os
from utils import load_config, ensure_dir_exists
import re

# Carregar configurações
config = load_config()
text_dir = config["paths"]["text_dir"]

def organize_text(text):
    # Dividir o texto em linhas e remover linhas vazias
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Remover espaços extras e caracteres indesejados
    cleaned_lines = []
    for line in lines:
        # Remover caracteres especiais indesejados, mantendo pontuação básica
        line = re.sub(r'[^\w\s.,;:()/-]', '', line)
        # Corrigir espaços múltiplos
        line = re.sub(r'\s+', ' ', line)
        # Corrigir pontuação
        line = re.sub(r'\s*([.,;:])\s*', r'\1 ', line)
        if line.strip():
            cleaned_lines.append(line.strip())
    
    # Juntar todas as linhas com ponto e vírgula
    return '; '.join(cleaned_lines)

def clean_text(text):
    # Remover caracteres especiais indesejados
    text = re.sub(r'[^\w\s.,;:()/-]', '', text)
    
    # Corrigir espaços múltiplos
    text = re.sub(r'\s+', ' ', text)
    
    # Corrigir pontuação
    text = re.sub(r'\s*([.,;:])\s*', r'\1 ', text)
    
    return text.strip()

# Processar todos os arquivos de texto
for filename in os.listdir(text_dir):
    if filename.endswith('.txt'):
        # Caminho do arquivo de texto
        text_path = os.path.join(text_dir, filename)
        
        # Ler o texto
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Aplicar pós-processamento (ex: remover espaços extras)
        text = ' '.join(text.split())
        
        # Salvar o texto corrigido
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Texto pós-processado salvo em: {text_path}")