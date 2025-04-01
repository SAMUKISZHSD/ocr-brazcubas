import torch
import easyocr
import cv2
import numpy as np
import re

# Inicializar o EasyOCR com configurações otimizadas para cupons fiscais
reader = easyocr.Reader(
    ['pt'],
    gpu=torch.cuda.is_available(),
    model_storage_directory='./models',
    download_enabled=True
)

def preprocess_receipt_image(image):
    """Pré-processa a imagem do cupom fiscal para melhor reconhecimento"""
    # Converter para escala de cinza
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Aumentar resolução
    scale = 3  # Aumentado para 3x
    enlarged = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Reduzir ruído preservando bordas
    denoised = cv2.fastNlMeansDenoising(enlarged, None, 15, 7, 21)
    
    # Melhorar nitidez
    kernel = np.array([[-1,-1,-1],
                      [-1, 9,-1],
                      [-1,-1,-1]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    
    # Melhorar contraste adaptativo
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(sharpened)
    
    # Binarização adaptativa
    binary = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        21,  # Aumentado para melhor adaptação
        11
    )
    
    # Aplicar dilatação para conectar componentes próximos
    kernel = np.ones((2,2), np.uint8)
    dilated = cv2.dilate(binary, kernel, iterations=1)
    
    return dilated

def extract_cnpj(text):
    """Extrai o CNPJ do texto"""
    patterns = [
        r'CNPJ[:\s]*(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\.\s]?\d{4}[-\.\s]?\d{2})',
        r'CNPJ\.?:?\s*(\d{2}\.?\d{3}\.?\d{3}\/?\d{4}\-?\d{2})',
        r'(\d{2}\.?\d{3}\.?\d{3}\/?\d{4}\-?\d{2})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            cnpj = match.group(1)
            cnpj = re.sub(r'[^\d]', '', cnpj)
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    return None

def extract_extract_number(text):
    """Extrai o número do extrato"""
    pattern = r'Extrato\s*No\.?\s*(\d+)'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1) if match else None

def extract_sat_number(text):
    """Extrai o número do SAT"""
    pattern = r'SAT\s*No\.?\s*(\d+)'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1) if match else None

def extract_date_time(text):
    """Extrai a data e hora"""
    pattern = r'(\d{2}/\d{2}/\d{4}\s*-?\s*\d{2}:\d{2}:\d{2})'
    match = re.search(pattern, text)
    return match.group(1) if match else None

def extract_total_value(text):
    """Extrai o valor total"""
    patterns = [
        r'TOTAL\s*R\$\s*(\d+[,\.]\d{2})',
        r'VALOR\s*TOTAL\s*R?\$?\s*(\d+[,\.]\d{2})',
        r'Qtd Total de Itens[\s\S]*?(\d+[,\.]\d{2})',
        r'VALOR\s*PAGO\s*R\$\s*(\d+[,\.]\d{2})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def extract_payment_method(text):
    """Extrai a forma de pagamento"""
    pattern = r'FORMA\s*PAGAMENTO\s*:\s*(.+?)(?:\n|$)'
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None

def extract_total_taxes(text):
    """Extrai o valor total dos tributos"""
    pattern = r'Valor\s*(?:aproximado\s*)?dos\s*tributos\s*(?:R\$)?\s*(\d+[,\.]\d{2})'
    match = re.search(pattern, text)
    return match.group(1) if match else None

def extract_products(text):
    """Extrai a lista de produtos de forma flexível"""
    products = []
    
    # Dividir o texto em linhas
    lines = text.split('\n')
    
    # Padrões flexíveis para produtos
    # Captura qualquer linha que tenha um número seguido de uma unidade e um valor
    patterns = [
        # Padrão mais comum: qualquer texto + quantidade + unidade + valor
        r'(.*?)[\s\.]+(\d+[,\.]?\d*)[\s\.]*(UN|U|KG|K|G|LT|L|CX|PC|PCT|EMB|ML|M)[\s\.]*?(\d+[,\.]?\d{2})',
        
        # Padrão alternativo: código no início + qualquer texto + quantidade + unidade + valor
        r'(\d+[\w\s\-]*?)[\s\.]+(\d+[,\.]?\d*)[\s\.]*(UN|U|KG|K|G|LT|L|CX|PC|PCT|EMB|ML|M)[\s\.]*?(\d+[,\.]?\d{2})',
        
        # Padrão para linhas sem unidade explícita
        r'(.*?)[\s\.]+(\d+[,\.]?\d*)[\s\.]*(\d+[,\.]?\d{2})'
    ]
    
    # Palavras que indicam que não é uma linha de produto
    skip_words = [
        'total', 'subtotal', 'desconto', 'acrescimo', 'troco', 'dinheiro', 'cartao',
        'valor', 'pago', 'tributos', 'cpf', 'cnpj', 'consumidor', 'sat', 'extrato'
    ]
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue
            
        # Verificar se a linha deve ser pulada
        should_skip = any(word in line.lower() for word in skip_words)
        if should_skip:
            continue
            
        # Tentar cada padrão
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                # Processar o texto principal (código e/ou descrição)
                text = groups[0].strip()
                
                # Tentar extrair código se existir
                code_match = re.match(r'^(\d+[A-Z0-9]*)(.*)', text)
                if code_match:
                    code = code_match.group(1)
                    description = code_match.group(2).strip()
                else:
                    code = None
                    description = text
                
                # Processar quantidade e valor
                if len(groups) == 4:  # Padrão com unidade
                    quantity = groups[1].replace(',', '.')
                    unit = groups[2].upper()
                    value = groups[3].replace(',', '.')
                else:  # Padrão sem unidade
                    quantity = groups[1].replace(',', '.')
                    unit = 'UN'  # Unidade padrão
                    value = groups[2].replace(',', '.')
                
                # Limpar e normalizar valores
                description = ' '.join(description.split())  # Normalizar espaços
                if description:  # Só adicionar se tiver descrição
                    product = {
                        'description': description.strip(),
                        'quantity': quantity,
                        'unit': unit,
                        'value': value
                    }
                    if code:
                        product['code'] = code.strip()
                    
                    products.append(product)
                break
    
    return products

def process_receipt(image):
    """Processa a imagem do cupom fiscal e retorna as informações extraídas"""
    try:
        # Pré-processar a imagem
        processed_image = preprocess_receipt_image(image)
        
        # Extrair texto usando EasyOCR com configurações flexíveis
        results = reader.readtext(
            processed_image,
            batch_size=8,
            detail=0,
            allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz,.-/():$%& ',
            paragraph=False,
            min_size=3,  # Muito flexível para caracteres pequenos
            contrast_ths=0.1,
            adjust_contrast=0.8,
            width_ths=0.3,  # Mais flexível
            height_ths=0.3,  # Mais flexível
            y_ths=0.2,  # Mais flexível para linhas
            x_ths=0.3,  # Mais flexível para caracteres
            slope_ths=0.3,
            add_margin=0.15,
            text_threshold=0.4  # Mais flexível para reconhecimento
        )
        
        # Juntar todo o texto e normalizar
        text = '\n'.join(line.strip() for line in results if line.strip())
        
        # Debug: mostrar texto extraído
        print("Texto extraído:")
        print(text)
        
        # Extrair informações
        data = {
            'success': True,
            'cnpj': extract_cnpj(text),
            'extractNumber': extract_extract_number(text),
            'satNumber': extract_sat_number(text),
            'dateTime': extract_date_time(text),
            'totalValue': extract_total_value(text),
            'paymentMethod': extract_payment_method(text),
            'totalTaxes': extract_total_taxes(text),
            'products': extract_products(text),
            'rawText': text  # Incluir texto bruto para debug
        }
        
        return data
        
    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        return {
            'success': False,
            'error': f'Erro ao processar cupom fiscal: {str(e)}',
            'rawText': text if 'text' in locals() else None
        } 