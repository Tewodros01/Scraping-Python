import customtkinter as ctk
from tkinter import ttk
from typing import List
from model.job_model import Job

class UnpostedJobsView(ctk.CTkFrame):
    """View for displaying and processing unposted jobs."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f5f5f5")
        self.controller = controller
        self.unposted_jobs = []

        # Configure the frame to fill the entire window
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Label for the unposted jobs title
        self.unposted_jobs_label = ctk.CTkLabel(self, text="Unposted Jobs List", text_color="#e74c3c", font=("Arial", 20))
        self.unposted_jobs_label.grid(row=0, column=0, pady=20, padx=10, sticky="n")

        # Table to display unposted jobs
        self.unposted_tree = ttk.Treeview(self, columns=("Title", "Company", "Reason"), show="headings")
        self.unposted_tree.heading("Title", text="Job Title")
        self.unposted_tree.heading("Company", text="Company")
        self.unposted_tree.heading("Reason", text="Reason")
        self.unposted_tree.grid(row=1, column=0, pady=10, padx=10, sticky="nsew")

        # Scrollbar for the unposted jobs table
        unposted_vsb = ttk.Scrollbar(self, orient="vertical", command=self.unposted_tree.yview)
        unposted_vsb.grid(row=1, column=1, sticky="ns")
        self.unposted_tree.configure(yscrollcommand=unposted_vsb.set)

        # Button to process unposted jobs
        self.process_unposted_button = ctk.CTkButton(self, text="Process Unposted Jobs", command=self.process_unposted_jobs, fg_color="#e74c3c", text_color="white")
        self.process_unposted_button.grid(row=2, column=0, pady=20, padx=10, sticky="s")

    def update_unposted_jobs(self, unposted_jobs: List[Job]):
        """Update the unposted jobs table in the UI."""
        self.unposted_jobs = unposted_jobs
        self.unposted_tree.delete(*self.unposted_tree.get_children())  # Clear the existing entries
        for job in unposted_jobs:
            self.unposted_tree.insert("", "end", values=(job.title, job.company, "Company Not Registered"))  # Example reason

    def process_unposted_jobs(self):
        """Create emails and register companies for unposted jobs."""
        if not self.unposted_jobs:
            print("No unposted jobs to process.")
            return

        for job in self.unposted_jobs:
            # Create email for the company
            # email = create_email(job.company)

            # Register the company as an employer in WordPress
            # employer_registration(job.company, email)

            # Post the job after registration
            # create_job_post(job)
            print(f"Processed job: {job.title} for company: {job.company}")

        print("Processed all unposted jobs.")
