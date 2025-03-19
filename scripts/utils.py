# scripts/utils.py
import yaml
import os

def load_config():
    """Carrega as configurações do arquivo YAML."""
    with open("./config/settings.yaml", "r") as file:
        config = yaml.safe_load(file)
    return config

def ensure_dir_exists(directory):
    """Cria um diretório se ele não existir."""
    if not os.path.exists(directory):
        os.makedirs(directory)