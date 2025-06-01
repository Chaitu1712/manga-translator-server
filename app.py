from flask import Flask, request, jsonify
from google import genai
import logging
import os
import threading 
import time
import json
from dotenv import load_dotenv
from google.genai import types

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
load_dotenv()
GOOGLE_API_KEY_OCR= os.getenv('GOOGLE_API_KEY_OCR')
GOOGLE_API_KEY_Trans= os.getenv('GOOGLE_API_KEY_Trans')
if not GOOGLE_API_KEY_OCR:
    logging.error("GOOGLE_API_KEY environment variable not set!")
clientOCR=genai.Client(api_key=GOOGLE_API_KEY_OCR)
clientTrans=genai.Client(api_key=GOOGLE_API_KEY_Trans)
last_request_time = time.time()-7.5
rate_limit_lock = threading.Lock()
MIN_INTERVAL = 7.0

@app.route('/upload', methods=['POST'])
def upload_image():
    logging.info("Received request for /upload")
    global last_request_time
    global rate_limit_lock
    if not GOOGLE_API_KEY_OCR:
        return jsonify({"status": "error", "message": "Google API key for OCR not configured"}), 500
    with rate_limit_lock:
        now = time.time()
        elapsed_time = now - last_request_time
        if elapsed_time < MIN_INTERVAL:
            wait_time = MIN_INTERVAL - elapsed_time
            logging.warning(f"Rate limit exceeded. Waiting {wait_time:.2f} seconds.")
            time.sleep(wait_time) 
            now = time.time() 
        last_request_time = now
    image_data = request.get_data()
    logging.info(f"Received image data of length: {len(image_data)} bytes")
    if not image_data:
        logging.warning("No image data received")
        return jsonify({"status": "error", "message": "No image data received"}), 400
    try:
        img=types.Part.from_bytes(
        data=image_data,
        mime_type='image/jpeg',
      ),
        promptOCR = """
        Extract all text from the image.
        Identify the primary language of the extracted text.
        Provide the output as a JSON object with the following keys:
        'ocr_text' (string): The extracted text.
        'detected_language' (string): The detected language code (e.g., 'ja' for Japanese, 'ko' for Korean, 'en' for English, 'ch_sim' for chinese simplified and 'ch_tra' for chinese traditional).
        """
        response = clientOCR.models.generate_content(
            model="gemini-2.0-flash",
            contents=[img,promptOCR]
        )
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            logging.warning(f"Gemini API blocked the prompt: {response.prompt_feedback}")
            return jsonify({"status": "error", "message": f"Prompt blocked: {response.prompt_feedback.block_reason}"}), 400
        try:
            response_text = response.text  
            start_index = response_text.find('{')
            end_index = response_text.rfind('}')
            if start_index == -1 or end_index == -1:
                raise ValueError("No JSON found in response")
            json_string = response_text[start_index:end_index+1]
            output = json.loads(json_string) 
            ocr_text = output.get('ocr_text', '')
            detected_language = output.get('detected_language', '')
            logging.info(f"Gemini OCR successful.")
            if not GOOGLE_API_KEY_Trans:
                return jsonify({"status": "error", "message": "Google API key for translation not configured"}), 500
            promptTranslation = f"""
            Translate the following text from {detected_language} e.g., 'ja' for Japanese, 'ko' for Korean, 'en' for English, 'ch_sim' for chinese simplified and 'ch_tra' for chinese traditional to English:
            {ocr_text}
            Provide the output as a JSON object with the
            following keys:
            'translated_text' (string): Only the translated text.
            """
            responseTranslation = clientTrans.models.generate_content(
                model="gemini-2.0-flash",
                contents=[promptTranslation]
            )
            translated_text = responseTranslation.text
            start_index = translated_text.find('{')
            end_index = translated_text.rfind('}')
            if start_index == -1 or end_index == -1:
                raise ValueError("No JSON found in translation response")
            json_string = translated_text[start_index:end_index+1]
            output = json.loads(json_string)
            translated_text = output.get('translated_text', '')
            logging.info(f"Gemini Translation successful.")
            return jsonify({
                "status": "success",
                "translated_text": translated_text
            })
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            logging.error(f"Failed to parse Gemini response: {e}", exc_info=True)
            logging.error(f"Raw response from Gemini: {response_text}")
            return jsonify({"status": "error", "message": f"Failed to parse Gemini response: {e}. Check server logs."}), 500
    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Error calling Gemini API: {e}"}), 500

@app.route('/')
def health_check():
    return "Server is running (Gemini Ready)", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)