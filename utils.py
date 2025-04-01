import os
import json

def load_config():
    """Carrega as configurações do sistema"""
    config = {
        "paths": {
            "processed_dir": "processed",
            "text_dir": "text_output"
        },
        "ocr": {
            "language": "pt"
        }
    }
    
    # Criar diretórios se não existirem
    for path in config["paths"].values():
        os.makedirs(path, exist_ok=True)
    
    return config

def ensure_dir_exists(directory):
    """Garante que um diretório existe, criando-o se necessário"""
    if not os.path.exists(directory):
        os.makedirs(directory) 