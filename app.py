from flask import Flask, render_template, request, jsonify, send_file
import os
import cv2
import numpy as np
from PIL import Image
import easyocr
import io
import csv
from datetime import datetime
import pytesseract
import re
from transformers import pipeline

# Configurar o caminho do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\josea\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializar EasyOCR uma única vez
reader = easyocr.Reader(['pt'])

# Carregar modelo de classificação de texto
print("Carregando modelo de IA leve...")
try:
    nlp = pipeline('text-classification', model='neuralmind/bert-base-portuguese-cased')
    print("Modelo de IA carregado com sucesso!")
except Exception as e:
    print(f"Erro ao carregar modelo de IA: {str(e)}")
    nlp = None

def improve_text_with_light_ai(text):
    """Melhora o texto usando um modelo leve de IA"""
    try:
        if not text or not nlp:
            return text
            
        # Dividir em linhas para processar cada uma
        lines = text.split('\n')
        improved_lines = []
        
        for line in lines:
            if not line.strip():
                continue
                
            # Verificar se a linha parece ter erro
            try:
                # Usar o modelo para classificar a qualidade do texto
                result = nlp(line)
                confidence = result[0]['score']
                
                # Se a confiança for baixa, aplicar correções adicionais
                if confidence < 0.8:
                    # Aplicar correções específicas para texto de baixa confiança
                    line = apply_advanced_corrections(line)
            except Exception as line_error:
                print(f"Erro ao processar linha com IA: {str(line_error)}")
            
            improved_lines.append(line)
        
        return '\n'.join(improved_lines)
        
    except Exception as e:
        print(f"Erro no processamento com IA leve: {str(e)}")
        return text

def apply_advanced_corrections(text):
    """Aplica correções avançadas em texto de baixa confiança"""
    # Correções específicas para números e caracteres especiais
    text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)  # Juntar números separados
    text = re.sub(r'[Nn](\s*)[°ºª]', r'Nº', text)  # Corrigir variações de "Nº"
    
    # Correções de palavras comuns em cupons fiscais
    replacements = {
        r'[Tt]0[Tt][Aa][Ll]': 'TOTAL',
        r'[Vv][Aa][Ll]0[Rr]': 'VALOR',
        r'[Cc][Uu][Pp]0[Mm]': 'CUPOM',
        r'[Ff][Ii][Ss][Cc][Aa][Ll]': 'FISCAL',
        r'[Ee][Ll][Ee][Tt][Rr]0[Nn][Ii][Cc]0': 'ELETRÔNICO'
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    
    return text

def process_text(text):
    """Processa e limpa o texto extraído, com foco em cupons fiscais"""
    try:
        if not text:
            return ""
            
        # Primeiro processamento básico
        processed_text = basic_text_processing(text)
        
        # Melhoramento com IA leve
        improved_text = improve_text_with_light_ai(processed_text)
        
        # Processamento final
        final_text = post_process_text(improved_text)
        
        return final_text
        
    except Exception as e:
        print(f"Erro no processamento de texto: {str(e)}")
        return text

def basic_text_processing(text):
    """Processamento básico inicial do texto"""
    lines = text.split('\n')
    processed_lines = []
    
    # Padrões específicos para cupons fiscais
    patterns = {
        'cnpj': r'CNPJ[:\s]*(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\.\s]?\d{4}[-\.\s]?\d{2})',
        'ie': r'IE[:\s]*(\d{2,3}[\.\s]?\d{3}[\.\s]?\d{3}[\.\s]?\d{3})',
        'im': r'IM[:\s]*(\d{2,3}[\.\s]?\d{3}[\.\s]?\d{3}[\.\s]?\d{3})',
        'cpf': r'CPF[:/\s]*(\d{3}[\.\s]?\d{3}[\.\s]?\d{3}[-\.\s]?\d{2})',
        'valor': r'R\$\s*(\d+[,\.]\d{2})',
        'sat': r'SAT\s*N[º°]?\.*\s*(\d{3}[\.\s]?\d{3}[\.\s]?\d{3})',
        'extrato': r'[Ee]xtrato\s*N[º°]?\.*\s*(\d+)'
    }
    
    # Campos já encontrados para evitar duplicatas
    found_fields = set()
    
    for line in lines:
        # Limpar a linha
        line = ' '.join(line.split())
        
        # Ignorar linhas vazias
        if not line.strip():
            continue
            
        # Processar campos específicos
        for field, pattern in patterns.items():
            if field not in found_fields:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    # Formatar valor encontrado
                    if field == 'cnpj':
                        value = re.sub(r'[^\d]', '', value)
                        value = f"{value[:2]}.{value[2:5]}.{value[5:8]}/{value[8:12]}-{value[12:]}"
                        line = f"CNPJ: {value}"
                    elif field in ['ie', 'im']:
                        value = re.sub(r'[^\d]', '', value)
                        line = f"{field.upper()}: {value}"
                    elif field == 'cpf':
                        value = re.sub(r'[^\d]', '', value)
                        value = f"{value[:3]}.{value[3:6]}.{value[6:9]}-{value[9:]}"
                        line = f"CPF: {value}"
                    elif field == 'valor':
                        value = value.replace(' ', '')
                        line = f"TOTAL: R$ {value}"
                    elif field == 'sat':
                        value = re.sub(r'[^\d]', '', value)
                        line = f"SAT Nº {value}"
                    elif field == 'extrato':
                        value = re.sub(r'[^\d]', '', value)
                        line = f"Extrato Nº {value}"
                    
                    found_fields.add(field)
                    break
        
        processed_lines.append(line)
    
    return '\n'.join(processed_lines)

def post_process_text(text):
    """Processamento final do texto"""
    lines = text.split('\n')
    final_lines = []
    
    for line in lines:
        # Corrigir erros comuns de OCR
        line = line.replace('0o', 'do')
        line = line.replace('0O', 'do')
        line = line.replace('l', 'I')
        line = line.replace('|', 'I')
        
        # Corrigir palavras específicas
        common_fixes = {
            'CUPOI': 'CUPOM',
            'EnTRx': 'EXTRATO',
            'lcõ': 'ICO',
            'Fantasla': 'Fantasia',
            'Razãp': 'Razão',
            'Sodat': 'Social',
            'Enderero': 'Endereço',
            'OBsERVAÇBES': 'OBSERVAÇÕES',
            'CONTRIBUNTE': 'CONTRIBUINTE',
            'Fromoçio': 'Promoção',
            'FREMIADO': 'PREMIADO',
            'supefmnescbdo': 'supermercado',
            'oonane': 'concorra',
            'primlo': 'prêmio',
            'dosüíbuto': 'dos tributos',
            'Ppom': 'cupom'
        }
        
        for wrong, correct in common_fixes.items():
            line = line.replace(wrong, correct)
        
        if line.strip():
            final_lines.append(line)
    
    # Remover duplicatas mantendo a ordem
    seen = set()
    unique_lines = []
    for line in final_lines:
        normalized = ''.join(c.lower() for c in line if c.isalnum())
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_lines.append(line)
    
    return '\n'.join(unique_lines)

def improve_text_with_ai(text):
    """Versão simplificada do melhoramento de texto"""
    try:
        # Aplicar regras básicas de correção
        improved_text = basic_text_improvement(text)
        return improved_text
    except Exception as e:
        print(f"Erro no processamento com IA: {str(e)}")
        return text

def basic_text_improvement(text):
    """Aplica melhorias básicas no texto sem usar modelos pesados"""
    lines = text.split('\n')
    improved_lines = []
    
    for line in lines:
        # Limpar espaços extras
        line = ' '.join(line.split())
        
        # Corrigir pontuação
        line = fix_punctuation(line)
        
        # Corrigir formatação de campos específicos
        if ':' in line:
            field, value = line.split(':', 1)
            field = field.strip()
            value = value.strip()
            
            # Aplicar formatações específicas
            if 'CPF' in field.upper():
                value = format_cpf(value)
            elif 'DATA' in field.upper():
                value = format_date(value)
            elif 'OFÍCIO' in field.upper():
                value = format_oficio(value)
            
            line = f"{field}: {value}"
        
        improved_lines.append(line)
    
    return '\n'.join(improved_lines)

def fix_punctuation(text):
    """Corrige problemas comuns de pontuação"""
    # Remover pontuação duplicada
    text = re.sub(r'[.,:;]{2,}', lambda m: m.group(0)[0], text)
    
    # Adicionar espaço após pontuação se não houver
    text = re.sub(r'([.,:;])([^\s])', r'\1 \2', text)
    
    # Remover espaços antes de pontuação
    text = re.sub(r'\s+([.,:;])', r'\1', text)
    
    return text

def format_oficio(value):
    """Formata número de ofício"""
    # Procurar padrão de número de ofício
    oficio_pattern = r'[Nn][º°]?\s*(\d+)[/.-]?(\d{4})?'
    match = re.search(oficio_pattern, value)
    if match:
        num = match.group(1)
        year = match.group(2) if match.group(2) else datetime.now().year
        return f"Nº {num}/{year}"
    return value

def try_different_methods(image):
    """Tenta diferentes métodos de pré-processamento e retorna o melhor resultado"""
    
    results = []
    
    # Definir todos os métodos de processamento
    methods = [
        {
            'name': "CLAHE + Threshold Adaptativo",
            'func': lambda img: process_clahe_adaptive(img)
        },
        {
            'name': "Otsu's Thresholding",
            'func': lambda img: process_otsu(img)
        },
        {
            'name': "Threshold Adaptativo Customizado",
            'func': lambda img: process_adaptive_custom(img)
        },
        {
            'name': "Equalização + Otsu",
            'func': lambda img: process_equalize_otsu(img)
        },
        {
            'name': "Binarização Local",
            'func': lambda img: process_local_binary(img)
        },
        {
            'name': "Contraste + Otsu",
            'func': lambda img: process_contrast_otsu(img)
        }
    ]
    
    # Processar a imagem com cada método
    for method in methods:
        try:
            processed = method['func'](image)
            # Converter para BGR para o OCR
            if len(processed.shape) == 2:  # Se for grayscale
                processed_bgr = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
            else:
                processed_bgr = processed
            
            # Realizar OCR para testar a qualidade
            test_text = perform_ocr(processed_bgr)
            if test_text:
                # Calcular pontuação baseada em heurísticas
                text_score = calculate_text_quality(test_text)
                image_score = evaluate_image_quality(processed, image)
                total_score = text_score * 0.6 + image_score * 0.4  # Peso maior para qualidade do texto
                
                results.append({
                    'name': method['name'],
                    'score': total_score,
                    'text_score': text_score,
                    'image_score': image_score,
                    'text': test_text,
                    'image': processed_bgr
                })
        except Exception as e:
            print(f"Erro no método {method['name']}: {str(e)}")
            continue
    
    # Se nenhum método funcionar, retornar a imagem original
    if not results:
        return image
    
    # Ordenar resultados por pontuação
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Retornar o resultado com a maior pontuação
    return results[0]['image']

def process_clahe_adaptive(img):
    """Método 1: CLAHE + Threshold Adaptativo"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    denoised = cv2.fastNlMeansDenoising(enhanced, None, 15, 7, 21)
    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 11)
    return thresh

def process_otsu(img):
    """Método 2: Otsu's Thresholding"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def process_adaptive_custom(img):
    """Método 3: Threshold Adaptativo com diferentes parâmetros"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray)
    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
    return thresh

def process_equalize_otsu(img):
    """Método 4: Equalização de Histograma + Otsu"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    equalized = cv2.equalizeHist(gray)
    _, thresh = cv2.threshold(equalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def process_local_binary(img):
    """Método 5: Binarização Local"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 115, 4)
    denoised = cv2.medianBlur(binary, 3)
    return denoised

def process_contrast_otsu(img):
    """Método 6: Contraste Aumentado + Otsu"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    alpha = 1.5  # Contraste
    beta = 0     # Brilho
    adjusted = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
    _, thresh = cv2.threshold(adjusted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def calculate_text_quality(text):
    """Calcula a qualidade do texto extraído com métricas melhoradas"""
    score = 0
    
    # Verificar comprimento do texto
    score += len(text) * 0.05  # Reduzido o peso do comprimento
    
    # Verificar quantidade de palavras válidas
    words = text.split()
    valid_words = sum(1 for word in words if len(word) > 2)
    score += valid_words * 0.3  # Reduzido o peso das palavras
    
    # Verificar caracteres válidos
    valid_chars = sum(1 for c in text if c.isalnum() or c.isspace() or c in '.,!?;:()[]{}')
    score += valid_chars * 0.2
    
    # Penalizar caracteres inválidos mais fortemente
    invalid_chars = len(text) - valid_chars
    score -= invalid_chars * 0.4
    
    # Verificar consistência do texto
    if len(words) > 0:
        # Calcular média de comprimento das palavras
        avg_word_length = sum(len(word) for word in words) / len(words)
        if 3 <= avg_word_length <= 15:  # Palavras com tamanho razoável
            score += 10
        
        # Verificar se há palavras comuns em português
        common_words = {'de', 'do', 'da', 'em', 'para', 'com', 'por', 'os', 'as', 'um', 'uma'}
        common_word_count = sum(1 for word in words if word.lower() in common_words)
        score += common_word_count * 5
    
    return max(score, 0)  # Garantir que a pontuação não seja negativa

def evaluate_image_quality(processed_image, original_image):
    """Avalia a qualidade da imagem processada em comparação com a original"""
    score = 0
    
    # Converter para escala de cinza se necessário
    if len(processed_image.shape) == 3:
        processed_gray = cv2.cvtColor(processed_image, cv2.COLOR_BGR2GRAY)
    else:
        processed_gray = processed_image
        
    if len(original_image.shape) == 3:
        original_gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
    else:
        original_gray = original_image
    
    # Avaliar contraste
    processed_contrast = np.std(processed_gray)
    score += min(processed_contrast / 30.0, 1.0) * 20
    
    # Avaliar distribuição de pixels (deve ter boa separação entre texto e fundo)
    hist = cv2.calcHist([processed_gray], [0], None, [256], [0, 256])
    hist_norm = hist.ravel() / hist.sum()
    peaks = np.where(hist_norm > np.mean(hist_norm) + np.std(hist_norm))[0]
    if len(peaks) >= 2:  # Boa separação entre texto e fundo
        score += 15
    
    # Avaliar nitidez
    laplacian = cv2.Laplacian(processed_gray, cv2.CV_64F).var()
    score += min(laplacian / 100.0, 1.0) * 10
    
    # Avaliar preservação de bordas
    edges_processed = cv2.Canny(processed_gray, 100, 200)
    edges_original = cv2.Canny(original_gray, 100, 200)
    edge_ratio = np.sum(edges_processed) / max(np.sum(edges_original), 1)
    score += min(edge_ratio, 1.0) * 15
    
    return score

def enhance_image(image):
    """Melhora a qualidade da imagem antes do pré-processamento"""
    try:
        # Converter para escala de cinza se for colorida
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Aumentar resolução da imagem
        scale = 2
        enlarged = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # Remover ruído preservando bordas
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

        # Remover ruído residual
        final = cv2.fastNlMeansDenoising(adjusted, None, 5, 7, 21)

        return final

    except Exception as e:
        print(f"Erro no melhoramento da imagem: {str(e)}")
        return image

def preprocess_image(image):
    """Pré-processa a imagem com foco em cupons fiscais"""
    try:
        # Primeiro melhorar a qualidade da imagem
        enhanced = enhance_image(image)
        
        # Aumentar contraste
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(enhanced)
        
        # Remover ruído
        denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
        
        # Binarização adaptativa
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,  # Reduzido para melhor detecção de texto pequeno
            2
        )
        
        # Operações morfológicas para limpar ruído
        kernel = np.ones((1,1), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
        
    except Exception as e:
        print(f"Erro no pré-processamento: {str(e)}")
        return image

def perform_ocr(image):
    """Realiza OCR otimizado para cupons fiscais"""
    try:
        # Configurações otimizadas para cupons fiscais
        easy_results = reader.readtext(
            image,
            paragraph=False,
            detail=1,
            width_ths=0.5,  # Aumentado para melhor detecção de linhas em cupons
            height_ths=0.5,  # Aumentado para melhor detecção de linhas em cupons
            contrast_ths=0.2,  # Reduzido para melhor detecção de texto em cupons
            text_threshold=0.6,  # Aumentado para reduzir ruído
            low_text=0.3,
            link_threshold=0.4,  # Aumentado para melhor agrupamento de texto
            add_margin=0.1
        )
        
        # Organizar resultados por posição
        sorted_results = sorted(easy_results, key=lambda x: (x[0][0][1], x[0][0][0]))
        
        lines = []
        current_y = -1
        current_line = []
        y_threshold = 10  # Reduzido para melhor separação de linhas em cupons
        
        for result in sorted_results:
            try:
                box = result[0]
                text = result[1]
                y = box[0][1]
                x = box[0][0]
                
                # Se mudou de linha ou é primeira linha
                if current_y == -1 or abs(y - current_y) > y_threshold:
                    if current_line:
                        current_line.sort(key=lambda x: x[1])
                        line_text = ' '.join(word[0] for word in current_line)
                        if line_text.strip():
                            lines.append(line_text)
                    current_line = [(text, x)]
                    current_y = y
                else:
                    current_line.append((text, x))
            except Exception as line_error:
                print(f"Erro ao processar linha: {str(line_error)}")
                continue
        
        # Processar última linha
        if current_line:
            current_line.sort(key=lambda x: x[1])
            line_text = ' '.join(word[0] for word in current_line)
            if line_text.strip():
                lines.append(line_text)
        
        return '\n'.join(lines)
        
    except Exception as e:
        print(f"Erro crítico no OCR: {str(e)}")
        raise Exception(f"Erro no processamento OCR: {str(e)}")

def validate_result(text):
    """Valida o resultado do OCR"""
    if not text:
        return False, "Nenhum texto foi extraído da imagem"
    
    # Remover espaços e quebras de linha extras
    text = ' '.join(text.split())
    
    # Verificar se o texto tem conteúdo significativo
    if len(text) < 5:
        return False, "Texto extraído muito curto. Tente melhorar a qualidade da imagem."
    
    # Verificar se o texto contém apenas caracteres válidos
    valid_chars = sum(1 for c in text if c.isalnum() or c.isspace() or c in '.,!?;:()[]{}')
    if valid_chars < len(text) * 0.4:  # Reduzido para 40% para aceitar mais variações
        return False, "Texto extraído contém muitos caracteres inválidos. Tente melhorar a qualidade da imagem."
    
    return True, "Texto válido"

def detect_document_type(image):
    """Detecta o tipo de documento"""
    # Implementar detecção de tipo de documento
    return "documento"

def get_suggestions(image):
    """Gera sugestões para melhorar a qualidade da imagem"""
    suggestions = []
    
    # Verificar resolução
    height, width = image.shape[:2]
    if width < 800 or height < 600:
        suggestions.append("A imagem tem baixa resolução. Tente usar uma imagem com maior resolução.")
    
    # Verificar contraste
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    contrast = np.std(gray)
    if contrast < 50:
        suggestions.append("O contraste da imagem está baixo. Tente melhorar a iluminação.")
    
    # Verificar nitidez
    laplacian = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian < 100:
        suggestions.append("A imagem está desfocada. Tente usar uma imagem mais nítida.")
    
    # Verificar brilho
    brightness = np.mean(gray)
    if brightness < 50:
        suggestions.append("A imagem está muito escura. Tente melhorar a iluminação.")
    elif brightness > 200:
        suggestions.append("A imagem está muito clara. Tente reduzir a iluminação.")
    
    return suggestions

def get_error_suggestions(error):
    """Retorna sugestões baseadas no tipo de erro"""
    suggestions = {
        "file_not_found": "Verifique se o arquivo foi enviado corretamente.",
        "invalid_file": "Use apenas arquivos de imagem (PNG, JPG, JPEG).",
        "file_too_large": "O arquivo é muito grande. Use uma imagem menor que 16MB.",
        "processing_error": "Ocorreu um erro ao processar a imagem. Tente novamente."
    }
    return suggestions.get(error, "Tente novamente com uma imagem diferente.")

def calculate_confidence(text):
    """Calcula um nível de confiança para o resultado do OCR"""
    # Implementar cálculo de confiança
    return 0.8

def process_license_plate(image):
    """Processa especificamente placas de carro"""
    try:
        # Converter para escala de cinza
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Aplicar blur para reduzir ruído
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        
        # Binarização adaptativa
        binary = cv2.adaptiveThreshold(
            blur,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            19,
            9
        )
        
        # Operações morfológicas para limpar a imagem
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrar contornos por área e proporção
        possible_plates = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 1000:  # Filtrar áreas muito pequenas
                x,y,w,h = cv2.boundingRect(cnt)
                aspect_ratio = float(w)/h
                if 2.0 <= aspect_ratio <= 5.0:  # Proporção típica de placas
                    possible_plates.append((x,y,w,h))
        
        best_text = ""
        highest_confidence = 0
        
        # Tentar OCR em cada região candidata
        for x,y,w,h in possible_plates:
            roi = image[y:y+h, x:x+w]
            
            # Aumentar resolução da ROI
            roi = cv2.resize(roi, (w*2, h*2), interpolation=cv2.INTER_CUBIC)
            
            # Tentar diferentes pré-processamentos
            preprocessed_images = [
                roi,  # Original
                cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY),  # Escala de cinza
                cv2.threshold(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],  # Otsu
            ]
            
            for prep_img in preprocessed_images:
                # Usar EasyOCR
                results = reader.readtext(prep_img)
                
                for (bbox, text, conf) in results:
                    # Limpar e validar o texto
                    cleaned_text = ''.join(e for e in text if e.isalnum())
                    
                    # Verificar se parece uma placa válida (3 letras + 4 números ou padrão Mercosul)
                    if len(cleaned_text) >= 7:
                        # Padrão antigo: 3 letras + 4 números
                        old_pattern = re.match(r'^[A-Z]{3}[0-9]{4}$', cleaned_text)
                        # Padrão Mercosul: 3 letras + 1 número + 1 letra + 2 números
                        mercosul_pattern = re.match(r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$', cleaned_text)
                        
                        if (old_pattern or mercosul_pattern) and conf > highest_confidence:
                            best_text = cleaned_text
                            highest_confidence = conf
        
        if best_text:
            # Formatar a placa encontrada
            if len(best_text) == 7:
                if best_text[3].isdigit() and best_text[4].isdigit():  # Padrão antigo
                    formatted_text = f"{best_text[:3]}-{best_text[3:]}"
                else:  # Padrão Mercosul
                    formatted_text = f"{best_text[:3]}{best_text[3]}{best_text[4]}{best_text[5:]}"
                return formatted_text, highest_confidence
        
        return "", 0
        
    except Exception as e:
        print(f"Erro no processamento da placa: {str(e)}")
        return "", 0

@app.route('/analyze-plate', methods=['POST'])
def analyze_plate():
    """Endpoint para análise de placas de carro"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
            
        # Ler a imagem
        in_memory_file = io.BytesIO()
        file.save(in_memory_file)
        data = np.frombuffer(in_memory_file.getvalue(), dtype=np.uint8)
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'error': 'Erro ao processar imagem'}), 400
            
        # Processar a placa
        plate_text, confidence = process_license_plate(image)
        
        if plate_text:
            return jsonify({
                'success': True,
                'plate': plate_text,
                'confidence': float(confidence)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Não foi possível identificar uma placa válida na imagem'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao processar imagem: {str(e)}'
        }), 500

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/ocr')
def ocr():
    return render_template('ocr.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'file_not_found',
            'message': 'Nenhum arquivo enviado'
        })
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'file_not_found',
            'message': 'Nenhum arquivo selecionado'
        })
    
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        return jsonify({
            'success': False,
            'error': 'invalid_file',
            'message': 'Formato de arquivo inválido'
        })
    
    try:
        # Ler a imagem
        image = cv2.imdecode(
            np.frombuffer(file.read(), np.uint8),
            cv2.IMREAD_COLOR
        )
        
        # Testar todos os métodos e obter os resultados
        method_results = []
        
        # Lista de métodos de processamento
        processing_methods = [
            {
                'name': "CLAHE + Threshold Adaptativo",
                'func': process_clahe_adaptive
            },
            {
                'name': "Otsu's Thresholding",
                'func': process_otsu
            },
            {
                'name': "Threshold Adaptativo Customizado",
                'func': process_adaptive_custom
            },
            {
                'name': "Equalização + Otsu",
                'func': process_equalize_otsu
            },
            {
                'name': "Binarização Local",
                'func': process_local_binary
            },
            {
                'name': "Contraste + Otsu",
                'func': process_contrast_otsu
            }
        ]
        
        for method in processing_methods:
            try:
                # Processar a imagem com o método atual
                processed = method['func'](image)
                
                # Converter para BGR se necessário
                if len(processed.shape) == 2:
                    processed_bgr = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
                else:
                    processed_bgr = processed
                
                # Realizar OCR
                text = perform_ocr(processed_bgr)
                if text:
                    # Calcular pontuações
                    text_score = calculate_text_quality(text)
                    image_score = evaluate_image_quality(processed, image)
                    total_score = text_score * 0.6 + image_score * 0.4
                    
                    method_results.append({
                        'name': method['name'],
                        'score': total_score,
                        'text_score': text_score,
                        'image_score': image_score,
                        'text': text
                    })
            except Exception as e:
                print(f"Erro no método {method['name']}: {str(e)}")
                continue
        
        # Ordenar resultados por pontuação
        method_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Usar o melhor método para o resultado final
        best_method = method_results[0] if method_results else None
        
        if best_method:
            # Processar e validar o texto do melhor método
            processed_text = process_text(best_method['text'])
            is_valid, validation_message = validate_result(processed_text)
            
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': 'processing_error',
                    'message': validation_message
                })
            
            # Detectar tipo de documento e gerar sugestões
            doc_type = detect_document_type(image)
            suggestions = get_suggestions(image)
            confidence = calculate_confidence(processed_text)
            
            # Análise de qualidade
            quality_metrics = {
                'best_method': best_method['name'],
                'best_method_score': best_method['score'],
                'best_method_text_score': best_method['text_score'],
                'best_method_image_score': best_method['image_score'],
                'validation_message': validation_message,
                'suggestions': suggestions
            }
            
            return jsonify({
                'success': True,
                'text': processed_text,
                'document_type': doc_type,
                'confidence': confidence,
                'quality_metrics': quality_metrics
            })
        else:
            return jsonify({
                'success': False,
                'error': 'processing_error',
                'message': 'Nenhum método conseguiu extrair texto válido da imagem'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'processing_error',
            'message': str(e)
        })

@app.route('/download/<format>', methods=['POST'])
def download_text(format):
    text = request.form.get('text', '')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if format == 'txt':
        output = io.StringIO()
        output.write(text)
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/plain',
            as_attachment=True,
            download_name=f'ocr_result_{timestamp}.txt'
        )
    
    elif format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        for line in text.split('\n'):
            writer.writerow([line])
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'ocr_result_{timestamp}.csv'
        )
    
    elif format == 'json':
        output = io.StringIO()
        output.write('{"text": "' + text.replace('"', '\\"').replace('\n', '\\n') + '"}')
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=f'ocr_result_{timestamp}.json'
        )
    
    return jsonify({'error': 'Formato não suportado'}), 400

@app.route('/check-tesseract')
def check_tesseract():
    try:
        # Verifica se o Tesseract está instalado
        version = pytesseract.get_tesseract_version()
        # Verifica se o pacote de idioma português está instalado
        langs = pytesseract.get_languages()
        has_portuguese = 'por' in langs
        
        return jsonify({
            'status': 'success',
            'tesseract_version': version,
            'has_portuguese': has_portuguese,
            'available_languages': langs
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/test-ocr', methods=['POST'])
def test_ocr():
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'file_not_found',
            'message': 'Nenhum arquivo enviado'
        })
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'file_not_found',
            'message': 'Nenhum arquivo selecionado'
        })
    
    try:
        # Ler a imagem original
        image = cv2.imdecode(
            np.frombuffer(file.read(), np.uint8),
            cv2.IMREAD_COLOR
        )
        
        # Testar todos os métodos e obter os resultados
        method_results = []
        
        # Lista de métodos de processamento
        processing_methods = [
            {
                'name': "CLAHE + Threshold Adaptativo",
                'func': process_clahe_adaptive
            },
            {
                'name': "Otsu's Thresholding",
                'func': process_otsu
            },
            {
                'name': "Threshold Adaptativo Customizado",
                'func': process_adaptive_custom
            },
            {
                'name': "Equalização + Otsu",
                'func': process_equalize_otsu
            },
            {
                'name': "Binarização Local",
                'func': process_local_binary
            },
            {
                'name': "Contraste + Otsu",
                'func': process_contrast_otsu
            }
        ]
        
        for method in processing_methods:
            try:
                # Processar a imagem com o método atual
                processed = method['func'](image)
                
                # Converter para BGR se necessário
                if len(processed.shape) == 2:
                    processed_bgr = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
                else:
                    processed_bgr = processed
                
                # Realizar OCR
                text = perform_ocr(processed_bgr)
                if text:
                    # Calcular pontuações
                    text_score = calculate_text_quality(text)
                    image_score = evaluate_image_quality(processed, image)
                    total_score = text_score * 0.6 + image_score * 0.4
                    
                    method_results.append({
                        'name': method['name'],
                        'score': total_score,
                        'text_score': text_score,
                        'image_score': image_score,
                        'text': text
                    })
            except Exception as e:
                print(f"Erro no método {method['name']}: {str(e)}")
                continue
        
        # Ordenar resultados por pontuação
        method_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Usar o melhor método para o resultado final
        best_method = method_results[0] if method_results else None
        
        if best_method:
            # Processar e validar o texto do melhor método
            processed_text = process_text(best_method['text'])
            is_valid, validation_message = validate_result(processed_text)
            
            # Análise de qualidade
            quality_metrics = {
                'best_method': best_method['name'],
                'best_method_score': best_method['score'],
                'best_method_text_score': best_method['text_score'],
                'best_method_image_score': best_method['image_score'],
                'all_methods': [{
                    'name': r['name'],
                    'score': r['score'],
                    'text_score': r['text_score'],
                    'image_score': r['image_score']
                } for r in method_results],
                'is_valid': is_valid,
                'validation_message': validation_message,
                'suggestions': get_suggestions(image)
            }
            
            return jsonify({
                'success': True,
                'quality_metrics': quality_metrics,
                'text': processed_text,
                'method_results': method_results
            })
        else:
            return jsonify({
                'success': False,
                'error': 'processing_error',
                'message': 'Nenhum método conseguiu extrair texto válido da imagem'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'processing_error',
            'message': str(e)
        })

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/plate')
def plate():
    return render_template('plate.html')

if __name__ == '__main__':
    app.run(debug=True)