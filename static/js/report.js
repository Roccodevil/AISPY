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

    // 4. Render full Intelligence Brief
    const reportText = data.final_report || data.reasoning || "No report narrative was generated.";
    document.getElementById('finalReport').textContent = reportText;
});