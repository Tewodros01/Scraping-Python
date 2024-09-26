import subprocess
import shlex
import json  # Import json to parse JSON output
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import time  # Import time for timestamp

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

def create_job_post(job):
    """Function to create a job post and set meta fields and terms using WP-CLI."""
    # Escape all input values to prevent syntax errors
    title = shlex.quote(job['title'])
    content = shlex.quote(job['content'])

    # Retrieve employer post using custom WordPress function
    employer_post = get_employer_post_by_email(job['email'])

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
            'jobsearch_field_job_apply_url': job['apply_url'],
            'jobsearch_field_job_apply_email': job['email'],
            'jobsearch_field_job_salary': 'sdf',
            'jobsearch_field_job_max_salary': 'sdf',
            'jobsearch_field_job_salary_type': 'sfdsd',
            'jobsearch_field_job_featured': 'off',
            'jobsearch_field_urgent_job':'off',
            'jobsearch_field_job_filled':'off',
            'jobsearch_field_job_posted_by': employer_post.get('employer_post_id'),
            # 'job_employer_email': job['email'],
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
            # "jobsearch_field_user_email": job['email'],
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
            "sector": job.get('job_sector', []),
            "jobtype": job.get('job_type', []),
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
        print(f"Failed to create job post: {job['title']}")
        print(f"Error: {e.stderr}")
    except Exception as e:
        print(f"An unexpected error occurred for job: {job['title']}")
        print(f"Error: {str(e)}")

def create_jobs(jobs_list):
    """Function to accept a list of jobs and process them in parallel."""
    # Use ThreadPoolExecutor to run jobs in parallel
    with ThreadPoolExecutor(max_workers=15) as executor:
        executor.map(create_job_post, jobs_list)

# Example call with jobs argument passed as a parameter
jobs = [
    {
        "title": "one to one",
        "content": "This is a job post content for Master Beat 2222.",
        "location": "New York",
        "email": "EMEBETWELDEHERYIZENGAW-BORAAMUSEMENTPARK@sebatsolutions.com",
        "job_sector": ["Information Technology"],
        "job_type": ["Full-Time", "Remote"],
        "qualifications": ["Bachelor's Degree in Computer Science", "Master's Degree in Computer Science"],
        "field_of_study": ["Computer Science", "Information Technology"],
        "apply_url": "https://",
        "salary": "333"
    }
]

# Now you can pass the jobs list to the create_jobs function
create_jobs(jobs)





