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

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def preprocess_image(image):
    """Pré-processa a imagem para melhorar a qualidade do OCR"""
    # Converter para escala de cinza
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Aumentar resolução se necessário
    height, width = gray.shape
    if width < 800 or height < 600:
        scale = 2
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Melhorar contraste usando CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Reduzir ruído preservando bordas
    denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
    
    # Aplicar threshold adaptativo com parâmetros mais suaves
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 15, 5
    )
    
    return thresh

def process_text(text):
    """Processa e limpa o texto extraído"""
    # Remover caracteres especiais
    text = ''.join(c for c in text if c.isprintable())
    
    # Corrigir espaçamento
    text = ' '.join(text.split())
    
    # Formatar quebras de linha
    text = text.replace('\n\n', '\n')
    
    # Corrigir pontuação
    text = text.replace(' ,', ',')
    text = text.replace(' .', '.')
    text = text.replace(' !', '!')
    text = text.replace(' ?', '?')
    
    return text.strip()

def validate_result(text):
    """Valida o resultado do OCR"""
    if not text:
        return False, "Nenhum texto foi extraído da imagem"
    
    # Remover espaços e quebras de linha extras
    text = ' '.join(text.split())
    
    # Verificar se o texto tem conteúdo significativo
    if len(text) < 5:  # Reduzido de 10 para 5 caracteres
        return False, "Texto extraído muito curto. Tente melhorar a qualidade da imagem."
    
    # Verificar se o texto contém apenas caracteres válidos
    valid_chars = sum(1 for c in text if c.isalnum() or c.isspace() or c in '.,!?;:()[]{}')
    if valid_chars < len(text) * 0.5:  # Pelo menos 50% dos caracteres devem ser válidos
        return False, "Texto extraído contém muitos caracteres inválidos. Tente melhorar a qualidade da imagem."
    
    return True, "Texto válido"

# Inicializar EasyOCR uma única vez
reader = easyocr.Reader(['pt'])

def perform_ocr(image):
    """Realiza OCR usando EasyOCR"""
    try:
        # Realizar OCR
        results = reader.readtext(image)
        
        # Extrair texto dos resultados
        text = '\n'.join([text[1] for text in results])
        
        return text
    except Exception as e:
        print(f"Erro no OCR: {str(e)}")
        return None

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
        # Ler e pré-processar a imagem
        image = cv2.imdecode(
            np.frombuffer(file.read(), np.uint8),
            cv2.IMREAD_COLOR
        )
        processed_image = preprocess_image(image)
        
        # Realizar OCR
        text = perform_ocr(processed_image)
        
        if text is None:
            return jsonify({
                'success': False,
                'error': 'processing_error',
                'message': 'Não foi possível extrair texto da imagem'
            })
        
        # Processar e validar o texto
        text = process_text(text)
        is_valid, validation_message = validate_result(text)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': 'processing_error',
                'message': validation_message
            })
        
        # Detectar tipo de documento e gerar sugestões
        doc_type = detect_document_type(image)
        suggestions = get_suggestions(image)
        confidence = calculate_confidence(text)
        
        return jsonify({
            'success': True,
            'text': text,
            'document_type': doc_type,
            'confidence': confidence,
            'suggestions': suggestions
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

if __name__ == '__main__':
    app.run(debug=True) 