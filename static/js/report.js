document.addEventListener('DOMContentLoaded', () => {
    const dataString = localStorage.getItem('aispy_report');
    if (!dataString) return window.location.href = "/";

    const data = JSON.parse(dataString);

    // Basic fields
    document.getElementById('reportId').innerText = "#" + Math.random().toString(36).substr(2, 9).toUpperCase();
    document.getElementById('reportDate').innerText = new Date().toLocaleDateString();
    document.getElementById('confidenceScore').innerText = data.confidence;
    document.getElementById('reasoningText').innerText = data.reasoning;
    document.getElementById('verdictStamp').innerText = data.verdict;
    
    // Verdict Color
    const v = data.verdict.toLowerCase();
    const stamp = document.getElementById('verdictStamp');
    if (v.includes('real')) stamp.className = "stamp real";
    else if (v.includes('fake')) stamp.className = "stamp fake";
    else stamp.className = "stamp warning";

    // --- NEW: Populate Sources List ---
    const sourceList = document.getElementById('sourceList'); // You need to add this ID to report.html
    if (sourceList) {
        if (data.context_sources && data.context_sources.length > 0) {
            let html = "";
            data.context_sources.forEach(src => {
                html += `<li class="mb-1"><a href="${src.url}" target="_blank" style="color: #3498db; text-decoration:none;">${src.title}</a></li>`;
            });
            sourceList.innerHTML = html;
        } else {
            sourceList.innerHTML = "<li>No specific web sources found.</li>";
        }
    }
});