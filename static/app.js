// Scrape Structure Form
const structureForm = document.getElementById('structureForm');
const structureLoading = document.getElementById('structureLoading');
const structureError = document.getElementById('structureError');
const structureResults = document.getElementById('structureResults');
let structureData = null;

structureForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const date = document.getElementById('date').value;
    const layer = document.getElementById('layer').value;

    structureError.style.display = 'none';
    structureResults.style.display = 'none';
    structureLoading.style.display = 'block';

    try {
        const response = await fetch('/api/scrape-structure', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ date, layer })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Error scraping structure');
        }

        structureData = data;
        displayStructureResults(data);
    } catch (error) {
        structureError.textContent = '❌ Error: ' + error.message;
        structureError.style.display = 'block';
    } finally {
        structureLoading.style.display = 'none';
    }
});

function displayStructureResults(data) {
    document.getElementById('structureCount').textContent = `Found ${data.count} results`;

    const table = document.getElementById('structureTable');
    table.innerHTML = '';

    // Create header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    data.columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create body
    const tbody = document.createElement('tbody');
    data.rows.slice(0, 50).forEach(row => {
        const tr = document.createElement('tr');
        data.columns.forEach(col => {
            const td = document.createElement('td');
            const value = row[col];

            if (col.includes('url') && value && value.startsWith('http')) {
                const a = document.createElement('a');
                a.href = value;
                a.textContent = value;
                a.target = '_blank';
                td.appendChild(a);
            } else {
                td.textContent = value || '-';
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    if (data.count > 50) {
        const note = document.createElement('p');
        note.style.marginTop = '10px';
        note.style.color = '#6b7280';
        note.textContent = `Showing first 50 of ${data.count} results`;
        structureResults.appendChild(note);
    }

    structureResults.style.display = 'block';
}

document.getElementById('structureExportBtn').addEventListener('click', () => {
    if (structureData) {
        exportCSV(structureData.rows, `rulebook_structure_${new Date().getTime()}.csv`);
    }
});

// Get Content Form
const contentForm = document.getElementById('contentForm');
const contentLoading = document.getElementById('contentLoading');
const contentError = document.getElementById('contentError');
const contentResults = document.getElementById('contentResults');
let contentData = null;

contentForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const url = document.getElementById('contentUrl').value;
    const type = document.getElementById('contentType').value;
    const singleRule = document.getElementById('singleRule').checked ? 'yes' : null;

    contentError.style.display = 'none';
    contentResults.style.display = 'none';
    contentLoading.style.display = 'block';

    try {
        const response = await fetch('/api/get-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url,
                type,
                single_rule_selector: singleRule
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Error fetching content');
        }

        contentData = data;
        displayContentResults(data);
    } catch (error) {
        contentError.textContent = '❌ Error: ' + error.message;
        contentError.style.display = 'block';
    } finally {
        contentLoading.style.display = 'none';
    }
});

function displayContentResults(data) {
    document.getElementById('contentCount').textContent = `Found ${data.count} results`;

    const table = document.getElementById('contentTable');
    table.innerHTML = '';

    // Create header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    data.columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create body
    const tbody = document.createElement('tbody');
    data.rows.slice(0, 50).forEach(row => {
        const tr = document.createElement('tr');
        data.columns.forEach(col => {
            const td = document.createElement('td');
            const value = row[col];

            if (col.includes('url') && value && value.startsWith('http')) {
                const a = document.createElement('a');
                a.href = value;
                a.textContent = value.substring(0, 60) + (value.length > 60 ? '...' : '');
                a.target = '_blank';
                a.title = value;
                td.appendChild(a);
            } else if (typeof value === 'boolean') {
                td.textContent = value ? '✓' : '✗';
            } else {
                td.textContent = value || '-';
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    if (data.count > 50) {
        const note = document.createElement('p');
        note.style.marginTop = '10px';
        note.style.color = '#6b7280';
        note.textContent = `Showing first 50 of ${data.count} results`;
        contentResults.appendChild(note);
    }

    contentResults.style.display = 'block';
}

document.getElementById('contentExportBtn').addEventListener('click', () => {
    if (contentData) {
        const contentType = document.getElementById('contentType').value;
        exportCSV(contentData.rows, `rulebook_${contentType}_${new Date().getTime()}.csv`);
    }
});

// Export to CSV
function exportCSV(rows, filename) {
    if (!rows || rows.length === 0) {
        alert('No data to export');
        return;
    }

    const df = rows;
    const headers = Object.keys(df[0]);

    let csv = headers.join(',') + '\n';

    df.forEach(row => {
        const values = headers.map(header => {
            const value = row[header];
            if (value === null || value === undefined) {
                return '';
            }
            const stringValue = String(value);
            if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
                return '"' + stringValue.replace(/"/g, '""') + '"';
            }
            return stringValue;
        });
        csv += values.join(',') + '\n';
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// Auto-fill example URL when structure results are clicked
document.addEventListener('click', (e) => {
    if (e.target.tagName === 'A' && e.target.closest('table')) {
        const href = e.target.getAttribute('href');
        if (href && href.startsWith('http')) {
            document.getElementById('contentUrl').value = href;
        }
    }
});
