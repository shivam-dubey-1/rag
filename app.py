from flask import Flask, render_template, request, jsonify
import requests
import os
import re
import string
import time
import logging

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt'}
API_URL = "http://"
MAX_TOKENS = 250  # Set the maximum token limit

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_file_content(file):
    return file.read().decode('utf-8')

def normalize_prompt(prompt):
    prompt = prompt.lower().strip()
    prompt = prompt.translate(str.maketrans('', '', string.punctuation))
    return prompt

def truncate_prompt(prompt, max_tokens):
    # Truncate prompt to a reasonable length based on token limits
    return prompt[:max_tokens]

def get_relevant_content(file_content, prompt):
    normalized_prompt = normalize_prompt(prompt)
    common_patterns = [r'what\sis\s', r'explain\s', r'define\s', r'what\sare\s']
    
    for pattern in common_patterns:
        normalized_prompt = re.sub(pattern, '', normalized_prompt)

    paragraphs = file_content.split('\n\n')
    relevant_paragraphs = []
    normalized_prompt = normalized_prompt.replace("key features of", "").strip()
    
    for paragraph in paragraphs:
        if re.search(r'\b' + re.escape(normalized_prompt) + r'\b', paragraph.lower()):
            relevant_paragraphs.append(paragraph.strip())

    return "\n\n".join(relevant_paragraphs) if relevant_paragraphs else paragraphs[0] if paragraphs else "No content available."

def get_response_from_api(prompt):
    try:
        # Truncate prompt to fit token limit
        truncated_prompt = truncate_prompt(prompt, MAX_TOKENS)
        data = {"prompt": truncated_prompt}

        # Print payload for debugging
        logging.debug("Sending payload: %s", data)

        response = requests.post(API_URL, json=data)
        response.raise_for_status()  # Raise HTTPError for bad responses

        if response.status_code == 200:
            data = response.json()
            if 'text' in data and isinstance(data['text'], list) and len(data['text']) > 0:
                full_text = data['text'][0]
                response_text = full_text.split("\n\n", 1)[-1] if "\n\n" in full_text else full_text
                return response_text
            else:
                return f"Error: Unexpected API response format. Received: {data}"
        else:
            return f"Error: API returned status code {response.status_code}. Response: {response.text}"
    except requests.exceptions.RequestException as e:
        logging.error("API request failed: %s", str(e))
        return f"Error: An exception occurred. Details: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        prompt = request.form.get('prompt', '')
        logging.debug(f"Received prompt: {prompt}")

        file_content = None
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            logging.debug(f"File received: {file.filename}")
            if file and allowed_file(file.filename):
                file_content = read_file_content(file)
                logging.debug(f"File content read, length: {len(file_content)}")

                relevant_content = get_relevant_content(file_content, prompt)
                logging.debug(f"Relevant content extracted, length: {len(relevant_content)}")
                response = get_response_from_api(f"{prompt}\n\n{relevant_content}")
            else:
                response = "Error: Invalid file type. Please upload a .txt file."
        else:
            logging.debug("No file received, using API")
            response = get_response_from_api(prompt)

        # Add a 3-second delay before returning the response
        # time.sleep(3)
        
        return jsonify({'response': response})
    
    return render_template('index.html')

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
