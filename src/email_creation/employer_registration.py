import subprocess
import shlex
import time

# SSH credentials and WP-CLI setup
ssh_user = "sebatjob"
ssh_host = "190.92.159.193"
ssh_port = "7822"
wp_path = "/home/sebatjob/play.7jobs.co"  # The path where WordPress is installed on the server

def run_wp_cli_command(command):
    """Executes a WP-CLI command via SSH and returns the output."""
    ssh_command = f"ssh -p {ssh_port} {ssh_user}@{ssh_host} {shlex.quote(command)}"
    try:
        result = subprocess.run(ssh_command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing WP-CLI command: {command}")
        print(f"Error: {e.stderr.strip()}")
        return None

def create_user(username, password, email, first_name, last_name, role='jobsearch_employer'):
    """Creates a new user in WordPress using WP-CLI."""
    
    # Check if the username or email already exists
    username_exists = run_wp_cli_command(f"wp user get {username} --field=user_login --path={wp_path}")
    email_exists = run_wp_cli_command(f"wp user get {email} --field=user_email --path={wp_path}")

    if username_exists or email_exists:
        print(f"Error: Username or email '{username}' or '{email}' already exists.")
        return None

    # Create the user
    command = (
        f"wp user create {username} {email} --user_pass={password} "
        f"--first_name={first_name} --last_name={last_name} --role={role} "
        f"--path={shlex.quote(wp_path)}"
    )
    user_creation_output = run_wp_cli_command(command)
    print(user_creation_output)
    if not user_creation_output:
        print(f"Error: User creation failed for {username}.")
        return None

    # Parse the user ID from the output
    user_id = user_creation_output.split()[-1]
    print(f"User '{username}' created successfully with ID: {user_id}")
    return user_id

def create_employer_post(user_id, company_name, company_detail, sector):
    """Creates a new employer post and assigns it to the user."""
    
    post_data_command = (
        f"wp post create --post_title={shlex.quote(company_name)} --post_content={shlex.quote(company_detail)} "
        f"--post_status=publish --post_author={shlex.quote(str(user_id))} --post_type=employer --path={shlex.quote(wp_path)} --porcelain"
    )

    # Create the post and capture the post ID
    post_id = run_wp_cli_command(post_data_command)
    
    if not post_id:
        print(f"Error: Failed to create employer post for user ID {user_id}.")
        return None
    user_candidate_id = run_wp_cli_command(f"wp eval 'echo jobsearch_get_user_candidate_id({user_id});' --path={wp_path}")
    if user_candidate_id:
        run_wp_cli_command(f"wp post delete {user_candidate_id} --force --path={wp_path}")
        print(f"Deleted candidate post ID {user_candidate_id} --path={wp_path}")

    # Update post meta fields
    run_wp_cli_command(f'wp user set-role {user_id} jobsearch_employer --path={wp_path}')
    run_wp_cli_command(f'wp user meta update {user_id} jobsearch_employer_id {post_id} --path={wp_path}')
    run_wp_cli_command(f'wp post meta update {post_id} jobsearch_user_id {user_id} --path={wp_path}')
    run_wp_cli_command(f'wp post meta update {post_id} employer_force_user_id {user_id} --path={wp_path}')
    run_wp_cli_command(f'wp post meta update {post_id} post_date {int(time.time())} --path={wp_path}')
    # run_wp_cli_command(f'wp post meta update {post_id} job_sector {shlex.quote(','.join(sector))} --path={wp_path}')
    run_wp_cli_command(f'wp post meta update {post_id} jobsearch_field_employer_approved "on" --path={wp_path}')
    run_wp_cli_command(f'wp eval jobsearch_get_user_candidate_id({user_id})')

  

    # Update user meta fields
    run_wp_cli_command(f"wp user meta update {user_id} jobsearch_employer_id {post_id} --path={wp_path}")

    print(f"Employer post created successfully for user ID {user_id} with post ID {post_id}")
    return post_id

def register_employer(username, password, email, first_name, last_name, company_name, company_detail, sectors):
    """Main function to register a user as an employer and create a post."""
    

    
    # Step 1: Create the user
    user_id = create_user(username, password, email, first_name, last_name)
    if not user_id:
        return

    # Step 2: Create the employer post
    post_id = create_employer_post(user_id, company_name, company_detail, sectors)
    if not post_id:
        return

    print(f"Employer '{username}' registered successfully with post ID: {post_id}")

    return username

def generate_username(company_name):
    """Generate a username by converting the company name to lowercase, removing spaces, and adding special characters."""
    # Convert to lowercase and replace spaces with underscores
    username = company_name.lower().replace(' ', '_')
    # Add a special character for demonstration (you can choose any rule here)
    return username

def split_company_name(company_name):
    """Split the company name into first and last name."""
    parts = company_name.split()
    if len(parts) > 1:
        first_name = parts[0]
        last_name = parts[1]
    else:
        first_name = parts[0]
        last_name = ""  # Empty last name if only one word is provided
    return first_name, last_name

def employer_registration(company_name, email):
    # Generate username
    username = generate_username(company_name)
    
    # Split company name into first name and last name
    first_name, last_name = split_company_name(company_name)
    print("Company name", email)
    print("Register Employer Email", email)
    # Example usage of the registration function
    register_employer(
        username=username, 
        password="securep3assword123", 
        email=email, 
        first_name=first_name, 
        last_name=last_name, 
        company_name=company_name, 
        company_detail="We specialize in web development services.", 
        sectors=["IT", "Marketing"]
    )


# company = "straight"

# created_email =  create_email(company)

# print(f"created email is {created_email}")

# employer_registration(company, created_email)


