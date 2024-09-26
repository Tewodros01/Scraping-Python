import sys
import os

# Add the 'src' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import subprocess
import shlex
import json  # Import json to parse JSON output
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import time  # Import time for timestamp
from typing import List

from model.job_model import Job  # Import the Job dataclass
from email_creation.employer_registration import employer_registration
from email_creation.email_creation import create_email
from model.job_model import Job  # Import the Job dataclass
from email_creation.account_checker import get_employer_post_by_fuzzy_email

import csv

from dataclasses import asdict  # Import asdict from dataclasses

# SSH credentials and WP-CLI setup
ssh_user = "sebatjob"
ssh_host = "190.92.159.193"
ssh_port = "7822"
wp_path = "/home/sebatjob/play.7jobs.co"  # The path where WordPress is installed on the server

# Calculate dynamic expiration dates (e.g., 30 days from now)
expiry_date = int((datetime.now() + timedelta(days=30)).timestamp())

def get_employer_post_by_email(email):
    """Function to retrieve employer post using the custom WordPress function and return the post meta."""
    # Escape email to prevent syntax errors
    escaped_email = shlex.quote(email)
    
    # PHP code to execute the custom function and get the post meta
    php_code = f"""
    $employer = search_employer_by_email('{escaped_email}');
    if ($employer && isset($employer->ID)) {{
        $user_id = get_post_meta($employer->ID, 'jobsearch_user_id', true);
        echo json_encode(array('employer_post_id' => $employer->ID, 'email' => $employer->user_email, 'jobsearch_user_id' => $user_id));
    }}
    """

    # Escape the PHP code for safe shell execution
    escaped_php_code = shlex.quote(php_code)

    # WP-CLI command to evaluate the PHP code
    wp_eval_command = f"wp eval {escaped_php_code} --path={shlex.quote(wp_path)}"

    # Print the WP-CLI command for debugging purposes
    print(f"Running WP-CLI command to retrieve employer post: {wp_eval_command}")

    # Run the WP-CLI command via SSH
    ssh_command = f"ssh -p {ssh_port} {ssh_user}@{ssh_host} {shlex.quote(wp_eval_command)}"

    # Execute the command using subprocess
    try:
        result = subprocess.run(ssh_command, shell=True, check=True, capture_output=True, text=True)
        employer_post_json = result.stdout.strip()  # Capture the post details in JSON format
        if employer_post_json:
            return json.loads(employer_post_json)  # Convert JSON string to Python dictionary
        return None
    except subprocess.CalledProcessError as e:
        print(f"Failed to retrieve employer post for email: {email}")
        print(f"Error: {e.stderr}")
        return None

def create_job_post(job: Job):
    """Function to create a job post and set meta fields and terms using WP-CLI."""
    # Execute the command using subprocess
    try:
      emailRespons = get_employer_post_by_fuzzy_email(job.company)
      # If the email is None, skip creating the job post or handle appropriately
      print('Employer email respons', emailRespons)
      if emailRespons is not None:
        title = shlex.quote(job.title)
        content = shlex.quote(job.content)

        # Retrieve employer post using custom WordPress function
        employer_post = get_employer_post_by_email(emailRespons)

        employer_email = employer_post.get('email') if employer_post else None
        employer_user_id = employer_post.get('jobsearch_user_id') if employer_post else None

        # Prepare WP-CLI command to create the post
        wp_cli_command = (
            f"wp post create --path={shlex.quote(wp_path)} --post_type=job "
            f"--post_title={title} --post_content={content} --post_status=publish --porcelain"
        )
        print("employer user id here")
        print(employer_post)

        # If the employer's user ID is available, add it to the command as post_author
        if employer_user_id:
            wp_cli_command += f" --post_author={employer_user_id}"

        # Print the WP-CLI command for debugging purposes
        print(f"Running WP-CLI command to create post: {wp_cli_command}")

        # Run the WP-CLI command via SSH and get the post ID
        ssh_command = f"ssh -p {ssh_port} {ssh_user}@{ssh_host} {shlex.quote(wp_cli_command)}"
        
        try:
            # Execute the command using subprocess and capture the post ID
            result = subprocess.run(ssh_command, shell=True, check=True, capture_output=True, text=True)
            post_id = result.stdout.strip()  # Post ID returned by WP-CLI
            
            print(f"Successfully created job post with ID: {post_id}")
            
            # Meta fields to be added to the post
            current_timestamp = str(int(time.time()))  # Current timestamp
            meta_fields = {
                # "job_location": job['location'],
                'jobsearch_field_job_publish_date': current_timestamp,
                'jobsearch_field_job_expiry_date': str(expiry_date),
                # 'job_expiry_days':'',
                'jobsearch_field_job_application_deadline_date':str(expiry_date),
                'jobsearch_field_job_apply_type': 'external',
                'jobsearch_field_job_apply_url': job.job_apply_url,
                'jobsearch_field_job_apply_email': emailRespons,
                'jobsearch_field_job_salary': 'sdf',
                'jobsearch_field_job_max_salary': 'sdf',
                'jobsearch_field_job_salary_type': 'sfdsd',
                'jobsearch_field_job_featured': 'off',
                'jobsearch_field_urgent_job':'off',
                'jobsearch_field_job_filled':'off',
                'jobsearch_field_job_posted_by': employer_post.get('employer_post_id'),
                # 'job_employer_email': emailRespons,
                # 'job_posted_empname': '',
                'jobsearch_field_job_status': 'approved',
                # 'jobsearch_field_location_location1': 'sdf',
                # 'jobsearch_field_location_location2': 'sfd',
                # 'jobsearch_field_location_location3': 'sdf',
                # 'jobsearch_field_location_address': 'sdfsd',
                # 'jobsearch_field_location_lat': 'sdf',
                # 'jobsearch_field_location_lng': 'sdfsd',


                "jobsearch_field_job_status": 'approved',
                "jobsearch_job_employer_status": 'approved',
                "jobsearch_job_presnt_status": 'approved',
                # "jobsearch_field_job_expiry_date": str(expiry_date),
                # "jobsearch_field_job_application_deadline_date": str(expiry_date),
                # "jobsearch_field_job_publish_date": current_timestamp,  # Add publish date meta field
                # "jobsearch_field_job_posted_by": employer_post.get('employer_post_id'),
                # "jobsearch_field_user_email": emailRespons,
                # "jobsearch_field_job_apply_url": "",
                # "jobsearch_field_job_apply_email":"",
                # "user_ID": 1569,
                # "post_ID": post_id,
                # "ID": post_id,
                # "post_author": 2433,
                # "post_status": "publish",
                # "post_status": "publish",
                # "visibility": "public",
                # "hidden_post_visibility": "public"
            }

            # Include employer_email if retrieved successfully
            if employer_email:
                meta_fields["employer_email"] = employer_email

            # Set meta fields for the created post using wp post meta set
            for meta_key, meta_value in meta_fields.items():
                # Prepare the WP-CLI command to set post meta
                wp_meta_command = (
                    f"wp post meta update {post_id} {shlex.quote(meta_key)} {meta_value} --path={shlex.quote(wp_path)}"
                )

                # Print the WP-CLI command for debugging purposes
                print(f"Running WP-CLI command to set meta: {wp_meta_command}")

                # Run the WP-CLI command via SSH without suppressing errors
                ssh_meta_command = f"ssh -p {ssh_port} {ssh_user}@{ssh_host} {shlex.quote(wp_meta_command)}"

                # Execute the command using subprocess
                try:
                    subprocess.run(ssh_meta_command, shell=True, check=True, capture_output=True, text=True)
                    print(f"Successfully set meta {meta_key} for post ID: {post_id}")
                except subprocess.CalledProcessError as e:
                    print(f"Failed to set meta {meta_key} for post ID: {post_id}")
                    print(f"Error: {e.stderr}")

            # Terms to be added to the post
            term_fields = {
                "sector": job.job_sector,
                "jobtype": job.job_type,
            }

            # Set terms for the created post using wp set term
            for taxonomy, terms in term_fields.items():
                # Ensure that `terms` is a list or convert it to a list if it's a single value
                # if not isinstance(terms, list):
                #     terms = [terms]  # Convert to list if it's not already

                # Iterate over each term in the list
                for term in terms:
                    # Prepare the WP-CLI command to set post terms
                    wp_term_command = (
                        f"wp post term set {post_id} {shlex.quote(taxonomy)} {shlex.quote(term)} --path={shlex.quote(wp_path)}"
                    )

                    # Print the WP-CLI command for debugging purposes
                    print(f"Running WP-CLI command to set term: {wp_term_command}")

                    # Run the WP-CLI command via SSH without suppressing errors
                    ssh_term_command = f"ssh -p {ssh_port} {ssh_user}@{ssh_host} {shlex.quote(wp_term_command)}"

                    # Execute the command using subprocess
                    try:
                        subprocess.run(ssh_term_command, shell=True, check=True, capture_output=True, text=True)
                        print(f"Successfully set term {term} for post ID: {post_id} under taxonomy {taxonomy}")
                    except subprocess.CalledProcessError as e:
                        print(f"Failed to set term {term} for post ID: {post_id} under taxonomy {taxonomy}")
                        print(f"Error: {e.stderr}")

        except subprocess.CalledProcessError as e:
            print(f"Failed to create job post: {job.title}")
            print(f"Error: {e.stderr}")
        except Exception as e:
            print(f"An unexpected error occurred for job: {job.title}")
            print(f"Error: {str(e)}")
        return None
      else:
        return job  
    except Exception as e:
      # Code that runs if an exception occurs
      print(f"An error occurred: {e}")
      return job
      
def create_jobs(jobs_list: List[Job]):
    """Function to accept a list of jobs and process them in parallel."""
    # Use ThreadPoolExecutor to run jobs in parallel
    unposted_jobs =[]
    with ThreadPoolExecutor(max_workers=15) as executor:
       results = executor.map(create_job_post, jobs_list)

    for job in results:
      print("Process email creation for unposted job")
      if job is not None:
          print("Process email creation", job.company)
          created_email = create_email(job.company)
          print("Created imale ", created_email)
          if created_email is not None:
              job.email = created_email
    
    for job in results:
      print("Process posting job for unposted job")
      if job.email is not None:
          print("Process unposted job", job.title)
          unposted_job = create_job_post(job)
          unposted_jobs.append(unposted_job)

    if unposted_jobs:
        export_unposted_jobs_to_csv(unposted_jobs)
        print(f"Exported {len(unposted_jobs)} unposted jobs to unposted_jobs.csv")

def export_unposted_jobs_to_csv(unposted_jobs: List[Job]):
    """Function to export unposted jobs to a CSV file."""
    csv_filename = "unposted_jobs.csv"
    field_names = [field.name for field in Job.__dataclass_fields__.values()]
    try:
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=field_names)
            writer.writeheader()
            for job in unposted_jobs:
                writer.writerow(asdict(job))
        print(f"Successfully exported unposted jobs to {csv_filename}")
    except Exception as e:
        print(f"Failed to export unposted jobs to CSV: {str(e)}")

# Create a list of Job instances
job_list: List[Job] = [
    Job(
        title="Software Engineer",
        content="We are looking for a skilled Software Engineer to join our team. You will be responsible for developing and maintaining web applications.",
        location="New York, USA",
        company="Tech Solutions Inc.",
        job_sector=["Information Technology", "Software Development"],
        job_type=["Full-time", "Remote"],
        qualifications=[
            "Bachelor's degree in Computer Science or related field",
            "3+ years of experience in software development"
        ],
        field_of_study=["Computer Science", "Information Technology"],
        career_level="Mid-level",
        job_apply_type="Email",
        experience="3-5 years",
        job_apply_url="https://www.techsolutions.com/jobs/apply",
        posted_time="2024-09-25T10:00:00Z",
        salary="$80,000 - $100,000 per year",
        skills=["Python", "Django", "JavaScript", "React"],
        expiry="2024-10-25T23:59:59Z"
    ),
    Job(
        title="Marketing Manager",
        content="We are seeking a Marketing Manager to oversee our marketing department and drive the growth of our brand.",
        location="London, UK",
        company="Global Marketing Ltd.",
        job_sector=["Marketing", "Business"],
        job_type=["Full-time", "On-site"],
        qualifications=[
            "Bachelor's degree in Marketing or Business Administration",
            "5+ years of experience in marketing management"
        ],
        field_of_study=["Marketing", "Business Administration"],
        career_level="Senior-level",
        job_apply_type="Website",
        experience="5-7 years",
        job_apply_url="https://www.globalmarketing.com/careers/apply",
        posted_time="2024-09-20T09:30:00Z",
        salary="£50,000 - £70,000 per year",
        skills=["SEO", "Content Marketing", "Digital Marketing", "Team Leadership"],
        expiry="2024-10-20T23:59:59Z"
    ),
    Job(
        title="Data Scientist",
        content="Join our team as a Data Scientist to analyze and interpret complex data sets to help us make better business decisions.",
        location="San Francisco, USA",
        company="Data Insights Corp.",
        job_sector=["Data Science", "Analytics"],
        job_type=["Full-time", "Hybrid"],
        qualifications=[
            "Master's degree in Data Science, Statistics, or a related field",
            "2+ years of experience in data analysis"
        ],
        field_of_study=["Data Science", "Statistics"],
        career_level="Mid-level",
        job_apply_type="Website",
        experience="2-4 years",
        job_apply_url="https://www.datainsights.com/careers/apply",
        posted_time="2024-09-22T15:45:00Z",
        salary="$90,000 - $120,000 per year",
        skills=["Python", "R", "Machine Learning", "Data Visualization"],
        expiry="2024-11-01T23:59:59Z"
    )
]

# Now you can pass the jobs list to the create_jobs function
# create_jobs(job_list)