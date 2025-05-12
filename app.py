from flask import Flask, request, jsonify
import logging
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Define the upload endpoint, accepting POST requests
@app.route('/upload', methods=['POST'])
def upload_image():
    logging.info("Received request for /upload")

    # Check if the request content type indicates image data (optional but good practice)
    # The Android app sends 'image/jpeg', Flask receives it as raw data.
    # Content-Type header might be available in request.headers
    content_type = request.headers.get('Content-Type')
    logging.info(f"Request Content-Type: {content_type}")

    # Get the raw data from the request body
    image_data = request.get_data()

    if not image_data:
        logging.warning("Received /upload request but no data in body.")
        return jsonify({"status": "error", "message": "No image data received"}), 400

    image_size_kb = len(image_data) / 1024
    logging.info(f"Successfully received image data: {image_size_kb:.2f} KB")

    # --- Next Steps (To be added later) ---
    # 1. Pass image_data to an OCR function
    # 2. Get text results
    # 3. Translate text
    # 4. Return translated text
    # --- End Next Steps ---

    # For now, just confirm receipt
    return jsonify({
        "status": "success",
        "message": f"Image received ({image_size_kb:.2f} KB)"
    }), 200

# Health check endpoint (good practice for Render)
@app.route('/')
def health_check():
    return "Server is running", 200

if __name__ == '__main__':
    # Render typically uses gunicorn, but this allows local running.
    # Render sets the PORT environment variable. Default to 5000 for local.
    port = int(os.environ.get('PORT', 5000))
    # Run on 0.0.0.0 to be accessible externally (needed for Render)
    app.run(debug=False, host='0.0.0.0', port=port)