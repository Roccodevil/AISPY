document.addEventListener('DOMContentLoaded', () => {
    // 1. Load data from localStorage
    const rawData = localStorage.getItem('aispy_report');
    if (!rawData) {
        alert("No report data found! Please run an analysis first.");
        window.location.href = '/';
        return;
    }

    const data = JSON.parse(rawData);

    // 2. Generate Report Metadata
    document.getElementById('reportId').innerText = 'AI-' + Math.random().toString(36).substr(2, 9).toUpperCase();
    document.getElementById('reportDate').innerText = new Date().toLocaleString();

    // 3. Populate Verdict & Confidence
    const stamp = document.getElementById('verdictStamp');
    stamp.innerText = data.verdict.toUpperCase();
    document.getElementById('confidenceScore').innerText = data.confidence;

    // Stamp Colors
    if (data.verdict.toLowerCase().includes('real')) {
        stamp.style.color = '#198754';
        stamp.style.borderColor = '#198754';
    } else if (data.verdict.toLowerCase().includes('fake') || data.verdict.toLowerCase().includes('misleading')) {
        stamp.style.color = '#dc3545';
        stamp.style.borderColor = '#dc3545';
    } else {
        stamp.style.color = '#ffc107';
        stamp.style.borderColor = '#ffc107';
    }

    // 4. Populate XAI Reasoning and Context
    document.getElementById('reasoningText').innerText = data.reasoning || "No reasoning provided.";
    document.getElementById('aiCaption').innerText = data.extracted_context || "No contextual data extracted.";
    document.getElementById('visualStatus').innerText = data.visual_evidence || "No pixel tampering detected.";

    // 5. Populate Sources
    const sourceList = document.getElementById('sourceList');
    sourceList.innerHTML = '';
    
    if (data.context_sources && data.context_sources.length > 0) {
        data.context_sources.forEach(source => {
            let li = document.createElement('li');
            li.style.marginBottom = "5px";
            li.innerHTML = `<a href="${source.url}" target="_blank" style="text-decoration:none; color:#0d6efd;">🔗 ${source.title || 'Source Link'}</a>`;
            sourceList.appendChild(li);
        });
    } else {
        sourceList.innerHTML = '<li>No reliable web sources found confirming or denying the context.</li>';
    }
});