from flask import Flask, render_template, request
import os
import io
import boto3
from botocore.exceptions import NoCredentialsError
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image 
import PyPDF2
import json


app = Flask(__name__)

S3_BUCKET_NAME = 'pandu-data'
S3_ACCESS_KEY = 'AKIA37YGOSG5DXITZNGD'
S3_SECRET_KEY = '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'
S3_REGION = 'us-east-1'

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def convert_to_pdf(input_file_path):
    file_name, file_extension = os.path.splitext(input_file_path)
    
    if file_extension.lower() in ['.jpg', '.jpeg', '.png']:
        image = Image.open(input_file_path)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f') 
        pdf_path = f"uploads/converted_{timestamp}.pdf"
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawImage(input_file_path, 100, 100, width=image.width, height=image.height)
        c.save()
        return pdf_path
    
    return None

def upload_to_s3(file_path, file_name):
    try:
        s3 = boto3.client('s3', aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY, region_name=S3_REGION)
        s3.upload_file(file_path, S3_BUCKET_NAME, file_name)
        return True
    except NoCredentialsError:
        return False

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/review')
def review():
    return render_template('reviewDetails.html')

def verifyDetails():
    return render_template('verifyDetails.html')

@app.route('/upload', methods=['POST'])
def upload():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
        uploaded_file.save(file_path)
        converted_pdf_path = convert_to_pdf(file_path)
        
        timestamp = str(datetime.now().strftime('%Y%m%d%H%M%S%f'))
        file_name_s3 = f"{timestamp}.pdf"
        if upload_to_s3(converted_pdf_path, file_name_s3):
            os.remove(converted_pdf_path)  
            return verifyDetails()
           
        else:
            return "Failed to upload the file to AWS S3."
    else:
        return "No file selected for upload."

@app.route('/submit')
def submit():
        return "Your electronic submission is successful please allow 24 to 48 hrs for validation"
@app.route('/process_pdf', methods=['POST'])
def process_pdf():
    file_name = request.form['file_name']  
    s3 = boto3.client('s3', aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY, region_name=S3_REGION)
    response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=file_name+'.json')
    pdf_content = response['Body'].read()

    pdf_data = extract_pdf_data(pdf_content)
    json_data = json.dumps(pdf_data)

    return json_data

def extract_pdf_data(pdf_content):
    pdf_data = {}
    pdf_reader = PyPDF2.PdfFileReader(io.BytesIO(pdf_content))
    for page_num in range(pdf_reader.numPages):
        page = pdf_reader.getPage(page_num)
        text = page.extractText()
    return pdf_data

if __name__ == '__main__':
    app.run(debug=True)