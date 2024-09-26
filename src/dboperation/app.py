from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import numpy as np
import os
from excell_operation import save_unsuccessful_job_to_excel
from sebatJobDataEncoder import JobDataEncoder
import json
from database_operations import db, save_job_to_db, Job

app = Flask(__name__)

# Configuration for MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://sebatsab_dataencoder:dataencoder@sebatsolutions.com:3306/sebatsab_job_data'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)

def organize_job_information_from_dict(job_data):
    # Create a DataFrame from the job_data dictionary
    df = pd.DataFrame([job_data])

    # Replace NaN values with empty strings
    df = df.fillna('')

    # Extract the first (and only) row as a dictionary
    job_data_cleaned = df.iloc[0].to_dict()

    organized_job = {
        'email': job_data_cleaned.get('email', ''),
        'password': job_data_cleaned.get('password', ''),
        'job_title': job_data_cleaned.get('job_title', ''),
        'job_description': job_data_cleaned.get('job_description', '').strip(),
        # 'application_deadline': "",
        'application_deadline': job_data_cleaned.get('application_deadline', '').strip(),
        'job_sector': sanitize_list_sector(job_data_cleaned.get('job_sector', '')),
        'job_type': sanitize_list_field(job_data_cleaned.get('job_type', '')),
        'skills': "",
        'job_apply_type': job_data_cleaned.get('job_apply_type', ''),
        'job_apply_url': job_data_cleaned.get('job_apply_url', ''),
        'job_apply_email': job_data_cleaned.get('job_apply_email', ''),
        'salary_type': job_data_cleaned.get('salary_type', ''),
        'min_salary': "",
        'max_salary': job_data_cleaned.get('max_salary', ''),
        'salary_currency': job_data_cleaned.get('salary_currency', ''),
        'salary_position': job_data_cleaned.get('salary_position', ''),
        'salary_separator': job_data_cleaned.get('salary_separator', ''),
        'salary_decimals': job_data_cleaned.get('salary_decimals', ''),
        'experience': job_data_cleaned.get('experience', ''),
        'gender': job_data_cleaned.get('gender', ''),
        'qualifications': sanitize_list_field(job_data_cleaned.get('qualifications')),
        'field_of_study': sanitize_list_field(job_data_cleaned.get('field_of_study')),
        'career_level': job_data_cleaned.get('career_level', ''),
        'country': job_data_cleaned.get('country', ''),
        'state': job_data_cleaned.get('state', ''),
        'city': job_data_cleaned.get('city', ''),
        'postal_code': job_data_cleaned.get('postal_code', ''),
        'full_address': job_data_cleaned.get('full_address', ''),
        'latitude': job_data_cleaned.get('latitude', ''),
        'longitude': job_data_cleaned.get('longitude', ''),
        'zoom': job_data_cleaned.get('zoom', '')
    }
    return organized_job

def sanitize_list_sector(data):
    """ Ensure the job sector data is always returned as a list. """
    if isinstance(data, list):
        return data
    return [data]

def sanitize_list_field(data):
    """ Convert potential NaN values or comma-separated strings in list fields to lists. """
    if isinstance(data, float) and np.isnan(data):
        return []  # Return an empty list if data is NaN
    elif isinstance(data, str):
        return [item.strip() for item in data.split(',')]  # Split the string into a list and strip whitespace
    elif isinstance(data, list):
        return data  # Return the list as-is if it's already a list
    return []  # Return an empty list as a fallback for any other data types

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.csv')):
        # Ensure the uploads directory exists
        uploads_dir = os.path.abspath('uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)

        file_path = os.path.join(uploads_dir, file.filename)
        file.save(file_path)

        if file.filename.endswith('.xlsx'):
            job_df = pd.read_excel(file_path)
        elif file.filename.endswith('.csv'):
            job_df = pd.read_csv(file_path)

        results = []
        error_logs = []

        for index, row in job_df.iterrows():
            job_data = row.to_dict()
            job_info = organize_job_information_from_dict(job_data)
            try:
                print("Orginized Job", job_info)

                encoder = JobDataEncoder(login_url='https://gamezone.7jobs.co', username=job_info['email'], password=job_info['password'])

                if encoder.login():
                    if encoder.navigate_to_post_job():
                        result = encoder.fill_post_job_form(job_info)
                        if result['status'] == 'success':
                            if encoder.logout():
                                results.append({
                                    "job_title": job_info['job_title'],
                                    "status": "success",
                                    "message": "Logged out successfully after posting job."
                                })
                            else:
                                error_message = "Failed to log out."
                                results.append({
                                    "job_title": job_info['job_title'],
                                    "status": "error",
                                    "message": error_message
                                })
                                error_logs.append({"job_title": job_info['job_title'], "error": error_message})
                        else:
                            results.append({
                                "job_title": job_info['job_title'],
                                "status": "error",
                                "message": result['message']
                            })
                            error_logs.append({"job_title": job_info['job_title'], "error": result['message']})
                    else:
                        error_message = "Failed to navigate to post job."
                        results.append({
                            "job_title": job_info['job_title'],
                            "status": "error",
                            "message": error_message
                        })
                        error_logs.append({"job_title": job_info['job_title'], "error": error_message})
                    encoder.close()
                else:
                    save_unsuccessful_job_to_excel(job_info)
                    error_message = "Failed to log in."
                    results.append({
                        "job_title": job_info['job_title'],
                        "status": "error",
                        "message": error_message
                    })
                    error_logs.append({"job_title": job_info['job_title'], "error": error_message})
                    encoder.close()
            except Exception as e:
                print(f"Error posting job : {e}")
        if error_logs:
            error_df = pd.DataFrame(error_logs)
            error_df.to_excel(os.path.join(uploads_dir, 'error_log.xlsx'), index=False)

        return jsonify(results)
    else:
        return jsonify({'error': 'File type not allowed. Please upload an Excel file.'}), 400

if __name__ == "__main__":
    # Create the database tables if they do not exist
    with app.app_context():
        db.create_all()

    app.run(debug=True)