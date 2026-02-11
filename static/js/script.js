let selectedFile = null;

// --- INPUT LOCKING LOGIC ---

document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const textInput = document.getElementById('textInput');
    const dropZone = document.getElementById('dropZone');

    // 1. If Text is typed, disable File Upload
    textInput.addEventListener('input', () => {
        if (textInput.value.length > 0) {
            dropZone.style.opacity = "0.5";
            dropZone.style.pointerEvents = "none";
        } else {
            dropZone.style.opacity = "1";
            dropZone.style.pointerEvents = "auto";
        }
    });

    // 2. If File is selected, disable Text Input
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            selectedFile = fileInput.files[0];
            
            // Visual Update
            document.getElementById('fileLabel').innerHTML = `✅ Ready: <strong>${selectedFile.name}</strong>`;
            dropZone.classList.add('upload-active');
            
            // Lock Text Input
            textInput.value = "";
            textInput.placeholder = "File attached. Text input disabled.";
            textInput.disabled = true;
        }
    });
});

async function startScan() {
    const resultBox = document.getElementById('resultBox');
    const loader = document.getElementById('loader');
    const textInput = document.getElementById('textInput');

    // Validation
    if (!textInput.value && !selectedFile) {
        alert("Please provide ONE input (File or Link).");
        return;
    }

    resultBox.innerHTML = "";
    loader.classList.remove('hidden');

    const formData = new FormData();
    if (selectedFile) formData.append('file', selectedFile);
    if (textInput.value) formData.append('input', textInput.value);

    try {
        const response = await fetch('/analyze', { method: 'POST', body: formData });
        const data = await response.json();
        
        loader.classList.add('hidden');

        if (data.error) {
            resultBox.innerHTML = `<div class="alert alert-danger"><strong>Error:</strong> ${data.error}</div>`;
            // Reset inputs on error
            textInput.disabled = false;
            textInput.placeholder = "Or paste a URL...";
            return;
        }

        localStorage.setItem('aispy_report', JSON.stringify(data));

        // Generate Source Links HTML
        let sourcesHtml = '';
        if (data.context_sources && data.context_sources.length > 0) {
            sourcesHtml = '<div class="mt-3"><small class="text-muted text-uppercase fw-bold">Context Sources:</small><ul class="list-unstyled mt-1">';
            data.context_sources.forEach(source => {
                sourcesHtml += `<li><a href="${source.url}" target="_blank" class="text-decoration-none small">🔗 ${source.title}</a></li>`;
            });
            sourcesHtml += '</ul></div>';
        }

        let colorClass = data.verdict.toLowerCase().includes('real') ? 'text-success' : 'text-danger';
        
        resultBox.innerHTML = `
            <div class="alert alert-light mt-4 text-start shadow-sm border">
                <h2 class="${colorClass} fw-bold text-center mb-3 text-uppercase">${data.verdict}</h2>
                <div class="progress mb-3" style="height: 10px;">
                    <div class="progress-bar bg-dark" style="width: ${data.confidence}%"></div>
                </div>
                <p class="lead small mb-2">${data.reasoning}</p>
                
                ${sourcesHtml}
                
                <hr>
                <div class="d-grid">
                    <a href="/report" class="btn btn-outline-dark fw-bold">📄 VIEW OFFICIAL CERTIFICATE</a>
                </div>
            </div>
        `;

    } catch (err) {
        loader.classList.add('hidden');
        alert("Server Error: " + err);
    }
}