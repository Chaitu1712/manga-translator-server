from flask import Flask, request, jsonify
import logging
import os
import easyocr
import numpy as np # EasyOCR often works with numpy arrays
import cv2 # OpenCV is needed by EasyOCR for image handling



app = Flask(__name__)

# Define the upload endpoint, accepting POST requests
@app.route('/upload', methods=['POST'])
def upload_image():
    logging.info("Received request for /upload")
    if reader is None:
        logging.error("OCR Reader not initialized. Cannot process image.")
        return jsonify({"status": "error", "message": "OCR service unavailable"}), 503 # Service Unavailable
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
    try:
        # Convert the raw image bytes to a format OpenCV (and EasyOCR) can read
        # 1. Convert bytes to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        # 2. Decode numpy array into OpenCV image format
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR) # Use IMREAD_COLOR for standard images

        if img_np is None:
             logging.error("Failed to decode image data using cv2.imdecode.")
             return jsonify({"status": "error", "message": "Failed to decode image data"}), 400

        # Perform OCR using EasyOCR
        # detail=0 means we only want the extracted text, not bounding boxes or confidence scores yet.
        # paragraph=True attempts to merge text lines into paragraphs, which might be helpful or hurtful depending on manga layout. Start with False or True and see.
        ocr_results = reader.readtext(img_np, detail=0, paragraph=False)

        # Join the list of detected text strings into a single block
        extracted_text = "\n".join(ocr_results) # Join lines with newline for readability

        logging.info(f"OCR successful. Extracted text length: {len(extracted_text)}")
        # Log first few characters of extracted text for debugging
        logging.debug(f"Extracted text sample: {extracted_text[:100]}...")

        # --- Next Steps (To be added later) ---
        # 1. Detect Language (if needed, e.g., if using multiple EasyOCR languages)
        # 2. Translate `extracted_text`
        # 3. Return translated text
        # --- End Next Steps ---

        # For now, return the raw extracted text
        return jsonify({
            "status": "success",
            "message": "OCR completed",
            "ocr_text": extracted_text # Send the extracted text back to the client
        }), 200

    except Exception as e:
        logging.error(f"Error during OCR processing: {e}", exc_info=True) # Log full traceback
        return jsonify({"status": "error", "message": f"OCR processing failed: {e}"}), 500

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