@echo off
echo Iniciando processo de OCR...

echo.
echo Executando preprocess.py...
python scripts/preprocess.py
if errorlevel 1 (
    echo Erro ao executar preprocess.py
    pause
    exit /b 1
)

echo.
echo Executando ocr.py...
python scripts/ocr.py
if errorlevel 1 (
    echo Erro ao executar ocr.py
    pause
    exit /b 1
)

echo.
echo Executando postprocess.py...
python scripts/postprocess.py
if errorlevel 1 (
    echo Erro ao executar postprocess.py
    pause
    exit /b 1
)

echo.
echo Processo concluído com sucesso!
pause 