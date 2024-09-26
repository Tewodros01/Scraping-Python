import customtkinter as ctk
from tkinter import ttk

class JobListingsView(ctk.CTkFrame):
    """View for displaying job listings after clicking 'View Details'."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f5f5f5")
        self.controller = controller

        # Label for the title of the view
        self.title_label = ctk.CTkLabel(self, text="Job Listings", font=("Arial", 18))  # Changed to 'font'
        self.title_label.grid(row=0, column=0, pady=10, padx=10, sticky="w")

        # Table to display job listings
        self.tree = ttk.Treeview(self, columns=(
            "Title", "Company", "Location", "Description", "Expiry", "Email", 
            "Job Sector", "Job Type", "Qualifications", "Field of Study", 
            "Career Level", "Job Apply Type", "Experience", "Job Apply URL", 
            "Posted Time", "Salary", "Skills"
        ), show="headings")

        # Define column headings
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        
        self.tree.grid(row=1, column=0, pady=20, padx=10, sticky="nsew", columnspan=3)

        # Scrollbar for the job listings table
        job_vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        job_vsb.grid(row=1, column=3, sticky="ns")
        self.tree.configure(yscrollcommand=job_vsb.set)

        # Back button to return to the scraper view
        self.back_button = ctk.CTkButton(self, text="Back to Scraper View", command=self.go_back)
        self.back_button.grid(row=2, column=0, pady=10, padx=10, sticky="w")

    def display_jobs(self,site_name, job_listings):
        """Display the scraped job listings in the job table."""
        # Clear previous entries
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new entries
        for job in job_listings:
            self.tree.insert("", "end", values=(
                job.title, 
                job.company, 
                job.location, 
                job.content, 
                job.expiry, 
                job.email, 
                ", ".join(job.job_sector) if job.job_sector else "",
                ", ".join(job.job_type) if job.job_type else "",
                ", ".join(job.qualifications) if job.qualifications else "",
                ", ".join(job.field_of_study) if job.field_of_study else "",
                job.career_level, 
                job.job_apply_type, 
                job.experience, 
                job.job_apply_url, 
                job.posted_time, 
                job.salary, 
                ", ".join(job.skills) if job.skills else ""
            ))

    def go_back(self):
        """Go back to the ScraperView."""
        self.controller.show_view("ScraperView")
