from fuzzywuzzy import process

def validate_job_details(job_details):
    valid_sectors = [
        "Accounting, Finance, and Insurance",
        "Administrative and Secretarial Services",
        "Advertising, Media Journalism, and Public Relations",
        "Architecture, Design, and Construction",
        "Banking, Investment, and Insurance",
        "Business and Management",
        "Communications, Marketing, and Sales",
        "Consultancy, Training, and Education",
        "Creative Arts, Event Management, and Entertainment",
        "Engineering and Technology",
        "Health and Wellness",
        "Hospitality, Tourism, and Customer Service",
        "Human Resources, Recruitment, and Organizational Development",
        "International Development and NGO",
        "Law, Legal Services, and Public Administration",
        "Logistics, Supply Chain, and Transportation",
        "Manufacturing and Production",
        "Natural and Social Sciences",
        "Product Development",
        "Product, Program, and Project Management",
        "Quality Assurance, Safety, and Compliance",
        "Relationship and Stakeholder Management",
        "Retail, Wholesale, and Inventory Management"
    ]

    valid_job_types = [
        "Commission",
        "Consultancy",
        "Contract",
        "Freelance",
        "Full time",
        "Hybrid",
        "Internship",
        "Part time",
        "Project Based",
        "Remote",
        "Temporary",
        "Volunteer"
    ]

    def get_closest_match(value, valid_values):
        match, score = process.extractOne(value, valid_values)
        return match if score >= 80 else None

    def are_valid_values(values, valid_values, field_name):
        invalid_values = []
        for value in values:
            closest_match = get_closest_match(value, valid_values)
            if not closest_match:
                invalid_values.append(value)
            else:
                print(f"{field_name}: '{value}' was corrected to '{closest_match}'")
        return invalid_values

    errors = []

    # Check job sectors, ensuring that each sector in the list is valid
    if 'job_sector' in job_details:
        invalid_sectors = are_valid_values(job_details['job_sector'], valid_sectors, "Job sector")
        if invalid_sectors:
            errors.append(f"Invalid job sector(s) found: {invalid_sectors}")

    # Check job types, ensuring that each type in the list is valid
    if 'job_type' in job_details:
        invalid_job_types = are_valid_values(job_details['job_type'], valid_job_types, "Job type")
        if invalid_job_types:
            errors.append(f"Invalid job type(s) found: {invalid_job_types}")

    return errors




