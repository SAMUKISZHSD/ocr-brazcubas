# OCR Brazcubas

Este é um projeto de OCR (Optical Character Recognition) desenvolvido para a Brazcubas, utilizando tecnologias modernas de processamento de imagem e reconhecimento de texto.

## 🚀 Funcionalidades

- Processamento de imagens utilizando OpenCV
- Reconhecimento de texto usando Tesseract OCR e EasyOCR
- Interface web desenvolvida com Flask
- Pré-processamento de imagens para melhorar a precisão do OCR
- Suporte a múltiplos formatos de imagem

## 🤖 Como funciona o OCR

O sistema utiliza uma combinação de técnicas avançadas de IA e processamento de imagem para realizar o reconhecimento de texto:

### Processamento de Imagem
1. **Pré-processamento**:
   - Redimensionamento automático da imagem
   - Remoção de ruídos
   - Melhoria de contraste
   - Binarização adaptativa

2. **Detecção de Texto**:
   - Utilização do OpenCV para detecção de regiões de texto
   - Segmentação de caracteres
   - Análise de layout do documento

### Reconhecimento de Texto
O sistema utiliza duas engines de OCR em paralelo para maior precisão:

1. **Tesseract OCR**:
   - Engine tradicional e robusta
   - Excelente para textos bem formatados
   - Suporte a múltiplos idiomas
   - Baseado em redes neurais convolucionais

2. **EasyOCR**:
   - Engine moderna baseada em deep learning
   - Melhor performance em textos manuscritos
   - Detecção automática de idioma
   - Utiliza modelos de IA pré-treinados

### Pós-processamento
- Correção de erros comuns de OCR
- Formatação do texto reconhecido
- Validação de resultados
- Geração de confiança para cada reconhecimento

### Tecnologias de IA Utilizadas
- Redes Neurais Convolucionais (CNN)
- Processamento de Linguagem Natural (NLP)
- Aprendizado de Máquina para correção de erros
- Modelos de deep learning para detecção de texto

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Tesseract OCR instalado no sistema
- Dependências listadas em `requirements.txt`

## 🛠️ Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/ocr-brazcubas.git
cd ocr-brazcubas
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Instale o Tesseract OCR:
- Windows: Baixe e instale do [site oficial](https://github.com/UB-Mannheim/tesseract/wiki)
- Linux: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`

## 💻 Como usar

1. Inicie o servidor Flask:
```bash
python app.py
```

2. Acesse a aplicação no navegador:
```
http://localhost:5000
```

3. Faça upload de uma imagem contendo texto
4. O sistema processará a imagem e retornará o texto reconhecido

## 🛡️ Tecnologias utilizadas

- Flask 2.0.1
- OpenCV 4.5.3
- Tesseract OCR 0.3.13
- EasyOCR 1.4.1
- NumPy 1.21.2
- scikit-image 0.22.0
- Pillow 8.3.2

## 👥 Autores

- [SAMUKISZHSD](https://github.com/SAMUKISZHSD)
