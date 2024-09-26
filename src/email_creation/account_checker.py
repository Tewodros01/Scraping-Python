import subprocess
import shlex
import json
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz, process  # Importing fuzzy matching libraries
import time

# SSH credentials and WP-CLI setup
ssh_user = "sebatjob"
ssh_host = "190.92.159.193"
ssh_port = "7822"
wp_path = "/home/sebatjob/play.7jobs.co"  # The path where WordPress is installed on the server

# Calculate dynamic expiration dates (e.g., 30 days from now)
expiry_date = int((datetime.now() + timedelta(days=30)).timestamp())

def get_all_employer_emails():
    """Function to retrieve all employer usernames and emails from WordPress using 'wp user list' command."""
    # WP-CLI command to list all users and get their email addresses and usernames
    wp_user_list_command = f"wp user list --fields=user_nicename,user_email --path={shlex.quote(wp_path)} --format=json"

    # Run the WP-CLI command via SSH
    ssh_command = f"ssh -p {ssh_port} {ssh_user}@{ssh_host} {shlex.quote(wp_user_list_command)}"

    try:
        result = subprocess.run(ssh_command, shell=True, check=True, capture_output=True, text=True)
        users_json = result.stdout.strip()  # Capture the list of users in JSON format
        if users_json:
            return json.loads(users_json)  # Convert JSON string to Python list of dictionaries
        return []
    except subprocess.CalledProcessError as e:
        print(f"Failed to retrieve users from WordPress.")
        print(f"Error: {e.stderr}")
        return []

def get_closest_username(input_username, user_list):
    """Function to perform fuzzy matching on the username list."""
    # Extract usernames for matching
    usernames = [user['user_nicename'] for user in user_list]
    
    # Use process.extractOne to find the closest match with a confidence score
    match, confidence = process.extractOne(input_username, usernames, scorer=fuzz.ratio)
    print(f"Best match: {match} with confidence: {confidence}")
    
    # If confidence is above 80%, consider it a match and return the associated email
    if confidence >= 80:
        for user in user_list:
            if user['user_nicename'] == match:
                return user['user_email']  # Return the email corresponding to the matched username
    return None

def get_employer_post_by_fuzzy_email(input_username):
    """Function to retrieve employer post using fuzzy matching."""
    # Retrieve all emails and usernames from WordPress
    all_users = get_all_employer_emails()

    if not all_users:
        print("No users found.")
        return None

    # Find the closest matching username and get the corresponding email
    matched_email = get_closest_username(input_username, all_users)

    if matched_email:
        # If a match is found, retrieve employer post for that email
        return (matched_email)

    print("No close match found.")
    return None

# Example usage
# input_username = "EMEBETWELDEHsERYIZENGAW-B 3ORAAMUSEMENTPARK"  # Replace with the username to be searched

# email = get_employer_post_by_fuzzy_email(input_username)
# print("Email ", email)


