document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.querySelector('.upload-area');
    const imageInput = document.getElementById('imageInput');
    const previewArea = document.getElementById('previewArea');
    const imagePreview = document.getElementById('imagePreview');
    const processButton = document.getElementById('processButton');
    const resetButton = document.getElementById('resetButton');
    const resultArea = document.getElementById('resultArea');
    const extractedText = document.getElementById('extractedText');
    const downloadTxt = document.getElementById('downloadTxt');
    const downloadCsv = document.getElementById('downloadCsv');
    const downloadJson = document.getElementById('downloadJson');

    let currentFile = null;
    let currentText = '';

    // Prevenir comportamento padrão de drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop zone quando item é arrastado sobre
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        uploadArea.classList.add('border-primary');
    }

    function unhighlight(e) {
        uploadArea.classList.remove('border-primary');
    }

    // Handle dropped files
    uploadArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    imageInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    // Funções para controlar o skeleton screen
    function showSkeleton(elementId) {
        document.getElementById(elementId).classList.add('active');
    }

    function hideSkeleton(elementId) {
        document.getElementById(elementId).classList.remove('active');
    }

    // Atualizar a função handleFiles
    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            const maxSize = 10 * 1024 * 1024; // 10MB
            const allowedTypes = ['image/jpeg', 'image/png', 'image/tiff', 'image/bmp', 'image/webp', 'application/pdf'];

            if (file.size > maxSize) {
                alert('O arquivo é muito grande. O tamanho máximo permitido é 10MB.');
                return;
            }

            if (!allowedTypes.includes(file.type)) {
                alert('Formato de arquivo não suportado. Formatos permitidos: JPG, PNG, TIFF, BMP, WEBP e PDF.');
                return;
            }

            showSkeleton('previewSkeleton');
            const reader = new FileReader();
            reader.onload = function(e) {
                const preview = document.getElementById('imagePreview');
                preview.src = e.target.result;
                preview.style.display = 'block';
                hideSkeleton('previewSkeleton');
                currentFile = file;
                previewArea.classList.remove('d-none');
            };
            reader.readAsDataURL(file);
        }
    }

    processButton.addEventListener('click', function() {
        if (currentFile) {
            uploadFile(currentFile);
        }
    });

    resetButton.addEventListener('click', function() {
        currentFile = null;
        currentText = '';
        imageInput.value = '';
        imagePreview.src = '';
        previewArea.classList.add('d-none');
        resultArea.classList.add('d-none');
        extractedText.textContent = '';
    });

    // Atualizar a função processImage
    async function processImage() {
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];
        
        if (!file) {
            alert('Por favor, selecione uma imagem primeiro.');
            return;
        }

        showSkeleton('textSkeleton');
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Erro ao processar a imagem');
            }

            const data = await response.json();
            document.getElementById('extractedText').textContent = data.text;
            document.getElementById('resultArea').style.display = 'block';
        } catch (error) {
            console.error('Erro:', error);
            alert('Erro ao processar a imagem. Por favor, tente novamente.');
        } finally {
            hideSkeleton('textSkeleton');
        }
    }

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        processButton.disabled = true;
        processButton.innerHTML = '<i class="bi bi-hourglass-split"></i> Processando...';

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            processButton.disabled = false;
            processButton.innerHTML = '<i class="bi bi-gear"></i> Processar Imagem';
            
            if (data.error) {
                alert(data.error);
            } else {
                currentText = data.text;
                extractedText.textContent = data.text;
                resultArea.classList.remove('d-none');
            }
        })
        .catch(error => {
            processButton.disabled = false;
            processButton.innerHTML = '<i class="bi bi-gear"></i> Processar Imagem';
            alert('Erro ao processar a imagem: ' + error);
        });
    }

    downloadTxt.addEventListener('click', function() {
        downloadText('txt');
    });

    downloadCsv.addEventListener('click', function() {
        downloadText('csv');
    });

    downloadJson.addEventListener('click', function() {
        downloadText('json');
    });

    function downloadText(format) {
        let content = '';
        let mimeType = '';
        let filename = `ocr_result_${new Date().toISOString().slice(0,19).replace(/[:]/g, '')}`;

        switch(format) {
            case 'txt':
                content = currentText;
                mimeType = 'text/plain';
                filename += '.txt';
                break;
            case 'csv':
                content = `Texto\n"${currentText.replace(/"/g, '""')}"`;
                mimeType = 'text/csv';
                filename += '.csv';
                break;
            case 'json':
                content = JSON.stringify({
                    text: currentText,
                    timestamp: new Date().toISOString(),
                    filename: currentFile ? currentFile.name : 'unknown'
                }, null, 2);
                mimeType = 'application/json';
                filename += '.json';
                break;
        }

        const blob = new Blob([content], { type: mimeType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
}); 