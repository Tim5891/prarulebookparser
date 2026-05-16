const runBtn = document.getElementById('runBtn');
const statusBox = document.getElementById('statusBox');
const progressText = document.getElementById('progressText');
const progressFill = document.getElementById('progressFill');
const errorDiv = document.getElementById('error');
const resultsDiv = document.getElementById('results');

let allResults = {};

runBtn.addEventListener('click', startScraping);

async function startScraping() {
    runBtn.disabled = true;
    statusBox.style.display = 'block';
    errorDiv.style.display = 'none';
    resultsDiv.style.display = 'none';
    allResults = {};

    try {
        // Step 1: Get latest rulebook date and scrape structure
        progressText.textContent = '📊 Step 1/5: Getting rulebook structure...';
        updateProgress(20);

        const structureResp = await fetch('/api/scrape-auto');
        const structureData = await structureResp.json();

        if (!structureResp.ok) {
            throw new Error(structureData.error || 'Failed to scrape structure');
        }

        allResults = structureData;

        // Update progress as we go
        updateProgress(100);
        progressText.textContent = '✓ Scraping complete!';

        displayResults();
    } catch (error) {
        errorDiv.textContent = '❌ Error: ' + error.message;
        errorDiv.style.display = 'block';
        progressText.textContent = '✗ Scraping failed';
    } finally {
        runBtn.disabled = false;
    }
}

function updateProgress(percent) {
    progressFill.style.width = percent + '%';
}

function displayResults() {
    const resultsList = document.getElementById('resultsList');
    resultsList.innerHTML = '';

    const items = [
        { label: 'Sectors', key: 'sectors_count' },
        { label: 'Parts', key: 'parts_count' },
        { label: 'Chapters', key: 'chapters_count' },
        { label: 'Rules', key: 'rules_count' },
    ];

    items.forEach(item => {
        if (item.key in allResults) {
            const div = document.createElement('div');
            div.className = 'result-item';
            div.innerHTML = `
                <span class="result-label">${item.label}:</span>
                <span class="result-value">${allResults[item.key]}</span>
            `;
            resultsList.appendChild(div);
        }
    });

    // Add download buttons
    const downloadBtns = document.getElementById('downloadButtons');
    downloadBtns.innerHTML = '';

    const files = [
        { name: 'sectors.csv', url: '/api/download/sectors' },
        { name: 'parts.csv', url: '/api/download/parts' },
        { name: 'chapters.csv', url: '/api/download/chapters' },
        { name: 'rules.csv', url: '/api/download/rules' },
        { name: 'links.csv', url: '/api/download/links' },
    ];

    files.forEach(file => {
        const btn = document.createElement('a');
        btn.className = 'download-btn';
        btn.href = file.url;
        btn.download = file.name;
        btn.textContent = `📥 ${file.name}`;
        downloadBtns.appendChild(btn);
    });

    resultsDiv.style.display = 'block';
}
