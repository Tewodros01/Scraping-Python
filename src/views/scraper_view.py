import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import threading
from typing import List
from datetime import datetime
from scrapers.behance_scraper import scrape_behance_jobs
from scrapers.hahujob_scraper import scrape_hahu_jobs
from scrapers.guilf_job_scraper import scrape_gulf_jobs
from scrapers.freelance_scraper import scrape_freelance_jobs
from scrapers.jobgether_job_scraper import scrape_jobgether_jobs
from scrapers.ethio_job_by_date import scrape_ethio_jobs
from scrapers.bayt_scraper_remote import scrape_bayt_jobs
from model.job_model import Job
from posting.job_posting_wpcli import create_jobs
from scrapers.telegram_scraper.Scrapper import Scrapper

class ScraperView(ctk.CTkFrame):
    """Scraper Management View Frame"""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f5f5f5")
        self.controller = controller
        self.scraped_jobs = {}  # Store scraped jobs per site
        self.total_sites = 9  # Total number of scraping sites
        self.completed_sites = 0  # Number of completed sites
        self.lock = threading.Lock()  # Lock for thread-safe updates

        # Configure the frame to fill the entire window
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Menu for selecting the scraping site
        self.selected_site = tk.StringVar(value="Behance")
        self.menu = ctk.CTkOptionMenu(self, values=["Behance", "LinkedIn", "Indeed", "Hahu Job", "Gulf Job", "Freelance Job", "Jobgether Job", "EthioJob", "Bayt","Telegram"],
                              command=self.update_site, 
                              variable=self.selected_site)
        self.menu.grid(row=1, column=0, pady=10, padx=10, sticky="nw")

        # Button to run the selected scraper
        self.scrape_button = ctk.CTkButton(self, text="Run Scraper", command=self.run_scraper, fg_color="#2e86de", text_color="white")
        self.scrape_button.grid(row=1, column=1, pady=10, padx=10, sticky="nw")

        # Button to run all scrapers
        self.run_all_button = ctk.CTkButton(self, text="Run All Scrapers", command=self.run_all_scrapers, fg_color="#2e86de", text_color="white")
        self.run_all_button.grid(row=1, column=2, pady=10, padx=10, sticky="nw")

        # Button to post all scraped jobs to WordPress
        self.post_jobs_button = ctk.CTkButton(self, text="Post All Jobs to WordPress", command=self.post_all_jobs, fg_color="#27ae60", text_color="white")
        self.post_jobs_button.grid(row=1, column=3, pady=10, padx=10, sticky="nw")

        # Progress bar (placed below the button)
        self.progress_bar = ctk.CTkProgressBar(self, fg_color="#dfe6e9", progress_color="#2e86de")
        self.progress_bar.grid(row=2, column=0, pady=10, padx=10, sticky="ew", columnspan=4)

        # Summary table to display job sites and total jobs scraped
        self.summary_tree = ttk.Treeview(self, columns=("Site", "Total Jobs", "Duration", "Details"), show="headings")
        self.summary_tree.heading("Site", text="Job Site")
        self.summary_tree.heading("Total Jobs", text="Total Jobs Scraped")
        self.summary_tree.heading("Duration", text="Duration")
        self.summary_tree.heading("Details", text="View Details")
        self.summary_tree.grid(row=3, column=0, pady=10, padx=10, sticky="nsew", columnspan=4)

        # Scrollbar for the summary table
        summary_vsb = ttk.Scrollbar(self, orient="vertical", command=self.summary_tree.yview)
        summary_vsb.grid(row=3, column=4, sticky="ns")
        self.summary_tree.configure(yscrollcommand=summary_vsb.set)

        # Bind double-click to view job listings details
        self.summary_tree.bind("<Double-1>", self.show_details)

    def update_site(self, choice):
        """Update the scraper button command based on the selected site."""
        # Update scraper button based on selection
        site_mapping = {
            "Behance": self.run_scraper,
            "LinkedIn": self.run_linkedin_scraper,
            "Indeed": self.run_indeed_scraper,
            "Hahu Job": self.run_hahu_job_scraper,
            "Gulf Job": self.run_gulf_job_scraper,
            "Freelance Job": self.run_freelance_job_scraper,
            "Jobgether Job": self.run_jobgether_scraper,
            "EthioJob": self.run_ethio_job_scraper,
            "Bayt": self.run_bayt_scraper, 
            "Telegram": self.run_telegram_scraper
        }
        if choice in site_mapping:
            self.scrape_button.configure(command=site_mapping[choice], text=f"Run {choice} Scraper")

    def run_scraper(self):
        """Run the scraper for Behance"""
        self.progress_bar.set(0)
        threading.Thread(target=self.scrape_behance).start()
    
    def run_bayt_scraper(self):
        """Run Bayt scraper in a separate thread."""
        self.progress_bar.set(0)
        threading.Thread(target=self.scrape_bayt).start()

    def run_linkedin_scraper(self):
        """Run LinkedIn scraper in a separate thread"""
        self.progress_bar.set(0)
        threading.Thread(target=self.scrape_linkedin).start()

    def run_indeed_scraper(self):
        """Run Indeed scraper in a separate thread"""
        self.progress_bar.set(0)
        threading.Thread(target=self.scrape_indeed).start()

    def run_hahu_job_scraper(self):
        """Run Hahu Job scraper in a separate thread"""
        self.progress_bar.set(0)
        threading.Thread(target=self.scrape_hahu_job).start()

    def run_gulf_job_scraper(self):
        """Run Gulf Job scraper in a separate thread"""
        self.progress_bar.set(0)
        threading.Thread(target=self.scrape_gulf_job).start()

    def run_freelance_job_scraper(self):
        """Run Freelance Job scraper in a separate thread"""
        self.progress_bar.set(0)
        threading.Thread(target=self.scrape_freelance_job).start()

    def run_jobgether_scraper(self):
        """Run Jobgether scraper in a separate thread"""
        self.progress_bar.set(0)
        threading.Thread(target=self.scrape_jobgether).start()

    def run_ethio_job_scraper(self):
        """Run EthioJob scraper in a separate thread"""
        self.progress_bar.set(0)
        threading.Thread(target=self.scrape_ethio_job).start()

    def run_all_scrapers(self):
        """Run all scrapers concurrently in separate threads and update the progress bar."""
        self.progress_bar.set(0)
        self.completed_sites = 0  # Reset completed sites counter
        scrapers = [
            self.scrape_behance,
            self.scrape_linkedin,
            self.scrape_indeed,
            self.scrape_hahu_job,
            self.scrape_gulf_job,
            self.scrape_freelance_job,
            self.scrape_jobgether,
            self.scrape_ethio_job,
            self.scrape_bayt
        ]
        # Start each scraper in a separate thread
        for scraper in scrapers:
            threading.Thread(target=scraper).start()

    def run_telegram_scraper(self):
        """Run the Telegram scraper directly without threads."""
        self.progress_bar.set(0)
        self.scrape_telegram()

    def scrape_telegram(self):
        """Scrape job listings from Telegram channels directly and update the summary table."""
        start_time = datetime.now()
        job_listings = Scrapper.get_jobs("freelance_ethio") 
        duration_seconds = (datetime.now() - start_time).total_seconds()
        duration_formatted = self.format_duration(duration_seconds)
        self.scraped_jobs["Telegram"] = job_listings
        self.update_summary_table("Telegram", len(job_listings), duration_formatted)
        self.increment_progress()

    def scrape_behance(self):
        """Scrape job listings from Behance and display them in the summary table."""
        self.scrape_and_update("Behance", scrape_behance_jobs)

    def scrape_linkedin(self):
        """Scrape LinkedIn job listings."""
        self.scrape_and_update("LinkedIn", lambda: [Job(title="Example Job", company="Example Company", location="Remote", content="Example Description")])

    def scrape_indeed(self):
        """Scrape Indeed job listings."""
        self.scrape_and_update("Indeed", lambda: [Job(title="Indeed Job", company="Indeed Company", location="Remote", content="Indeed Job Description")])

    def scrape_hahu_job(self):
        """Scrape job listings from Hahu Job."""
        self.scrape_and_update("Hahu Job", scrape_hahu_jobs)

    def scrape_gulf_job(self):
        """Scrape job listings from Gulf Job."""
        self.scrape_and_update("Gulf Job", scrape_gulf_jobs)

    def scrape_freelance_job(self):
        """Scrape job listings from Freelance Job."""
        self.scrape_and_update("Freelance Job", scrape_freelance_jobs)

    def scrape_jobgether(self):
        """Scrape job listings from Jobgether."""
        self.scrape_and_update("Jobgether", scrape_jobgether_jobs)

    def scrape_ethio_job(self):
        """Scrape job listings from EthioJob."""
        self.scrape_and_update("EthioJob", scrape_ethio_jobs)

    def scrape_bayt(self):
        """Scrape job listings from Bayt."""
        self.scrape_and_update("Bayt", scrape_bayt_jobs)

    def scrape_and_update(self, site_name, scraper_function):
        """Scrape job listings and update the summary table with progress."""
        start_time = datetime.now()
        job_listings = scraper_function(progress_callback=self.update_progress)
        duration_seconds = (datetime.now() - start_time).total_seconds()
        duration_formatted = self.format_duration(duration_seconds)
        self.scraped_jobs[site_name] = job_listings
        self.update_summary_table(site_name, len(job_listings), duration_formatted)
        self.increment_progress()

    def increment_progress(self):
        """Increment the progress bar and handle completion updates."""
        with self.lock:
            self.completed_sites += 1
            progress = self.completed_sites / self.total_sites
            self.progress_bar.set(progress)
            if self.completed_sites == self.total_sites:
                print("All scrapers have finished.")

    def update_summary_table(self, site_name, total_jobs, duration):
        """Update the summary table with site name, total jobs, and duration of scraping."""
        self.summary_tree.insert("", "end", values=(site_name, total_jobs, duration, "View Details"))

    def show_details(self, event):
        """Show job listings in a separate view."""
        selected_item = self.summary_tree.selection()[0]
        site_name = self.summary_tree.item(selected_item, "values")[0]
        job_listings = self.scraped_jobs.get(site_name, [])

        # Switch to the JobListingsView and display the job listings
        self.controller.show_job_listings(site_name, job_listings)

    def update_progress(self, progress):
        """Update the progress bar value."""
        self.progress_bar.set(progress)

    def post_all_jobs(self):
        """Function to post all scraped jobs to WordPress."""
        all_jobs = []
        for site_name, job_list in self.scraped_jobs.items():
            all_jobs.extend(job_list)
        
        if not all_jobs:
            print("No jobs to post.")
            return

        # Call create_jobs function from the WordPress posting script
        print(f"Posting {len(all_jobs)} jobs to WordPress...")
        create_jobs(all_jobs)  # Call your create_jobs function from the WP-CLI script
        print("All jobs posted successfully.")

    def format_duration(self, duration_seconds):
        """Format duration from seconds to minutes and hours as needed."""
        if duration_seconds < 60:
            return f"{duration_seconds:.2f} seconds"
        elif duration_seconds < 3600:
            minutes = duration_seconds / 60
            return f"{minutes:.2f} minutes"
        else:
            hours = duration_seconds / 3600
            return f"{hours:.2f} hours"
