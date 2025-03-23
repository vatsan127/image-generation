from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
import PyPDF2
import os
import tempfile
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import time
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'pdf_to_image_secret_key'


def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        # Only read first page for front page content
        if len(pdf_reader.pages) > 0:
            page = pdf_reader.pages[0]
            text = page.extract_text()
            # Split into words and limit to first 50 words
            words = text.split()[:50]
            text = ' '.join(words)
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None
    return text

def generate_image_prompt(pdf_text):
    summary = ' '.join(pdf_text.split()[:30])

    prompt = f"""Create a simple document:

Essential requirements:
- Light gradient background from white to very light blue
- Clean professional look with subtle geometric pattern
- Three clear text sections on top of background:
  1. Title (large black heading - first 5-7 words)
  2. Main text (dark gray content - 15-20 words)
  3. Bottom text (small gray text - 5-8 words)

{summary}
"""
    return prompt


# Function to generate image using Gemini API
def generate_image(prompt):
    try:
        # Get API key from environment
        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            print("Gemini API key is missing. Please set it in the environment variables.")
            return None

        # Initialize the Gemini client
        client = genai.Client(api_key=api_key)

        # Generate the image
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['Text', 'Image']
            )
        )

        # Extract the image from the response
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image = Image.open(BytesIO((part.inline_data.data)))
                image_bytes = BytesIO()
                image.save(image_bytes, format='PNG')
                image_bytes.seek(0)
                return image_bytes

        return None

    except Exception as e:
        print(f"Error generating image: {e}")
        return None


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'pdf_file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['pdf_file']

        # Check if the user selected a file
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # Check if the file is a PDF
        if file and file.filename.endswith('.pdf'):
            # Save the file temporarily
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, file.filename)
            file.save(file_path)
            logging.debug(f"File saved to {file_path}")

            # Generate a session ID to track this file
            session_id = str(time.time())
            app.config[f'pdf_file_{session_id}'] = file_path
            logging.debug(f"Session ID {session_id} created for file {file_path}")

            return redirect(url_for('process_pdf', filename=file.filename, session_id=session_id))
        else:
            flash('Please upload a PDF file')
            return redirect(request.url)

    return render_template('index.html')


@app.route('/process/<filename>', methods=['GET', 'POST'])
def process_pdf(filename):
    try:
        session_id = request.args.get('session_id')
        file_path = app.config.get(f'pdf_file_{session_id}')
        logging.debug(f"Processing file {file_path} for session ID {session_id}")

        if not file_path or not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            flash('File not found or has expired')
            return redirect(url_for('index'))

        with open(file_path, 'rb') as pdf_file:
            pdf_text = extract_text_from_pdf(pdf_file)

        if pdf_text is None:
            flash('Error processing PDF file')
            return redirect(url_for('index'))

        prompt = generate_image_prompt(pdf_text)
        image_bytes = generate_image(prompt)

        if image_bytes is None:
            flash('Error generating image')
            return redirect(url_for('index'))

        temp_img_path = os.path.join(tempfile.gettempdir(), f'generated_image_{session_id}.png')
        with open(temp_img_path, 'wb') as f:
            f.write(image_bytes.getvalue())

        app.config[f'generated_image_{session_id}'] = temp_img_path

        return redirect(url_for('result', session_id=session_id, prompt=prompt))

    except Exception as e:
        logging.error(f"Error in process_pdf: {e}")
        flash('Error processing file')
        return redirect(url_for('index'))


@app.route('/result/<session_id>')
def result(session_id):
    img_path = app.config.get(f'generated_image_{session_id}')
    prompt = request.args.get('prompt', '')

    if not img_path or not os.path.exists(img_path):
        flash('Image not found or has expired')
        return redirect(url_for('index'))

    # Read the image
    with open(img_path, 'rb') as f:
        img_data = f.read()

    # Convert to base64 for display
    img_base64 = base64.b64encode(img_data).decode('utf-8')

    return render_template('result.html',
                           img_base64=img_base64,
                           session_id=session_id,
                           prompt=prompt)


@app.route('/download/<session_id>')
def download_image(session_id):
    img_path = app.config.get(f'generated_image_{session_id}')

    if not img_path or not os.path.exists(img_path):
        flash('Image not found or has expired')
        return redirect(url_for('index'))

    try:
        return_value = send_file(img_path, as_attachment=True, download_name='course_image.png')
        cleanup_files(session_id)  # Clean up after successful download
        return return_value
    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        flash('Error downloading image')
        return redirect(url_for('index'))


def cleanup_files(session_id):
    """Clean up files for a specific session"""
    pdf_path = app.config.get(f'pdf_file_{session_id}')
    img_path = app.config.get(f'generated_image_{session_id}')

    for path in [pdf_path, img_path]:
        if path and os.path.exists(path):
            try:
                if os.path.isdir(path):
                    for file in os.listdir(path):
                        os.unlink(os.path.join(path, file))
                    os.rmdir(path)
                else:
                    os.unlink(path)
            except Exception as e:
                logging.error(f"Error cleaning up file {path}: {e}")

    # Remove from app config
    app.config.pop(f'pdf_file_{session_id}', None)
    app.config.pop(f'generated_image_{session_id}', None)


if __name__ == '__main__':
    app.run(debug=True)
