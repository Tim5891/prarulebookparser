import os
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
import pandas as pd
import io
from prarulebook import get_structure, get_content, recode_layer

__version__ = "1.0.0"

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Store scrape results
SCRAPE_RESULTS = {}


@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@app.route('/api/scrape-auto', methods=['GET', 'POST'])
def scrape_auto():
    """Automatically scrape entire rulebook with default settings."""
    try:
        print("Starting automatic scrape...")

        # Use a known good date - 18-06-2019 is a stable snapshot
        rulebook_date = "18-06-2019"
        print(f"Scraping with date: {rulebook_date}")

        # Scrape structure at chapter level
        print("Getting chapters...")
        print(f"  Calling get_structure({rulebook_date}, layer='chapter')...")
        chapters = get_structure(rulebook_date, layer="chapter")
        print(f"  Type of chapters: {type(chapters)}")
        print(f"  Chapters shape: {chapters.shape if hasattr(chapters, 'shape') else 'N/A'}")
        print(f"  Chapters columns: {list(chapters.columns) if hasattr(chapters, 'columns') else 'N/A'}")
        chapters_count = len(chapters)
        print(f"  Found {chapters_count} chapters")
        if chapters_count == 0:
            print(f"  WARNING: No chapters found! Chapters content: {chapters}")

        # Get parts and sectors from the same structure
        print("Getting parts and sectors...")
        try:
            parts = chapters[['part_name', 'part_url', 'sector_name', 'sector_url']].drop_duplicates()
            parts_count = len(parts)
            sectors = chapters[['sector_name', 'sector_url']].drop_duplicates()
            sectors_count = len(sectors)
            print(f"  Found {sectors_count} sectors, {parts_count} parts")
        except Exception as e:
            print(f"  Error extracting parts/sectors: {e}")
            parts = pd.DataFrame()
            sectors = pd.DataFrame()
            parts_count = 0
            sectors_count = 0

        # Scrape text content from first 10 chapters (to keep it reasonable)
        print("Getting rule text...")
        rules_text = []
        for i, chapter_url in enumerate(chapters['chapter_url'][:10]):
            if pd.notna(chapter_url):
                try:
                    print(f"  Processing chapter {i+1}...")
                    text = get_content(chapter_url, content_type="text")
                    if text is not None and not text.empty:
                        # Convert all columns to string to avoid type issues
                        for col in text.columns:
                            text[col] = text[col].astype(str)
                        rules_text.append(text)
                except Exception as e:
                    print(f"  Skipping chapter {i+1}: {type(e).__name__}: {str(e)}")
                    continue

        if rules_text:
            rules_df = pd.concat(rules_text, ignore_index=True)
            rules_count = len(rules_df)
        else:
            rules_df = pd.DataFrame()
            rules_count = 0
        print(f"  Found {rules_count} rules")

        # Scrape links from first 20 chapters
        print("Getting links...")
        links_data = []
        for i, chapter_url in enumerate(chapters['chapter_url'][:20]):
            if pd.notna(chapter_url):
                try:
                    links = get_content(chapter_url, content_type="links")
                    if links is not None and not links.empty:
                        links_data.append(links)
                except Exception as e:
                    print(f"  Skipping links for chapter {i+1}: {str(e)}")
                    continue

        if links_data:
            links_df = pd.concat(links_data, ignore_index=True)
        else:
            links_df = pd.DataFrame()

        # Store results globally for download
        SCRAPE_RESULTS['sectors'] = sectors
        SCRAPE_RESULTS['parts'] = parts
        SCRAPE_RESULTS['chapters'] = chapters
        SCRAPE_RESULTS['rules'] = rules_df
        SCRAPE_RESULTS['links'] = links_df

        result = {
            'sectors_count': sectors_count,
            'parts_count': parts_count,
            'chapters_count': chapters_count,
            'rules_count': rules_count,
            'links_count': len(links_df),
            'date': rulebook_date
        }

        print("Scraping complete!")
        return jsonify(result)

    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error: {error_msg}")
        print(traceback.format_exc())
        return jsonify({'error': f'Scraping failed: {error_msg}'}), 500


@app.route('/api/download/<dtype>')
def download_data(dtype):
    """Download scraped data as CSV."""
    try:
        if dtype not in SCRAPE_RESULTS:
            return jsonify({'error': f'No {dtype} data available'}), 404

        df = SCRAPE_RESULTS[dtype]

        if df.empty:
            return jsonify({'error': f'No {dtype} data to download'}), 404

        # Create CSV in memory
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=rulebook_{dtype}.csv'}
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint for Railway."""
    return jsonify({'status': 'ok', 'version': __version__})


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
