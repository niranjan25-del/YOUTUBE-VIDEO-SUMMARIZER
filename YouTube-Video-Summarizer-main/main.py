from flask import Flask, jsonify, request, render_template, flash, redirect, url_for
from video import VideoProcessor
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Initialize video processor
processor = VideoProcessor()

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/process", methods=['POST'])
def process_video():
    try:
        # Get form data
        url = request.form.get('url', '').strip()
        method = request.form.get('method', 'extractive')
        percentage = int(request.form.get('percentage', 25))
        
        # Validate inputs
        if not url:
            flash('Please provide a YouTube URL', 'error')
            return redirect(url_for('index'))
        
        if not url.startswith(('https://www.youtube.com/', 'https://youtu.be/')):
            flash('Please provide a valid YouTube URL', 'error')
            return redirect(url_for('index'))
        
        logger.info(f"Processing video: {url} with method: {method}")
        
        # Process the video
        result = processor.process_video(url, method, percentage / 100.0)
        
        return render_template('result.html', 
                             url=url, 
                             text=result['text'], 
                             summary=result['summary'],
                             method=method,
                             percentage=percentage)
    
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        flash(f'Error processing video: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route("/api/process", methods=['POST'])
def api_process_video():
    """API endpoint for processing videos"""
    try:
        data = request.get_json()
        url = data.get('url')
        method = data.get('method', 'extractive')
        percentage = data.get('percentage', 25) / 100.0
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        result = processor.process_video(url, method, percentage)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs('./videos', exist_ok=True)
    os.makedirs('./audios', exist_ok=True)
    os.makedirs('./audios/chunks', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)