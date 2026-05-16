import os
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import pandas as pd
import io
from prarulebook import get_structure, get_content, recode_layer

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max


@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@app.route('/api/scrape-structure', methods=['POST'])
def scrape_structure():
    """Scrape rulebook structure."""
    try:
        data = request.get_json()
        rulebook_date = data.get('date')
        layer = data.get('layer', 'chapter')

        if not rulebook_date:
            return jsonify({'error': 'Date is required'}), 400

        # Validate date format
        try:
            datetime.strptime(rulebook_date, "%d-%m-%Y")
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use dd-mm-yyyy'}), 400

        if layer not in ['sector', 'part', 'chapter', 'rule']:
            return jsonify({'error': 'Invalid layer'}), 400

        print(f"Scraping structure for {rulebook_date} at {layer} level...")
        structure = get_structure(rulebook_date, layer=layer)

        # Convert to JSON-serializable format
        result = {
            'rows': structure.to_dict('records'),
            'columns': list(structure.columns),
            'count': len(structure)
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/get-content', methods=['POST'])
def get_content_route():
    """Get content (text or links) from a URL."""
    try:
        data = request.get_json()
        url = data.get('url')
        content_type = data.get('type', 'text')
        single_rule = data.get('single_rule_selector')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        print(f"Fetching {content_type} from {url}...")
        content = get_content(url, content_type=content_type, single_rule_selector=single_rule)

        result = {
            'rows': content.to_dict('records'),
            'columns': list(content.columns),
            'count': len(content)
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export-csv', methods=['POST'])
def export_csv():
    """Export data as CSV."""
    try:
        data = request.get_json()
        rows = data.get('rows')
        filename = data.get('filename', 'export.csv')

        if not rows:
            return jsonify({'error': 'No data to export'}), 400

        df = pd.DataFrame(rows)

        # Create CSV in memory
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint for Railway."""
    return jsonify({'status': 'ok'})


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
