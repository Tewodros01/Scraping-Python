import sys
import os
import customtkinter as ctk

# Add the 'src' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.view_manager import ViewManager
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.scraper_view import ScraperView
from views.job_listings_view import JobListingsView  

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

def main():
    """Main entry point for the Job Scraper Admin Panel application."""
    root = ctk.CTk()
    root.title("Job Scraper Admin Panel")
    root.geometry('800x600')

    # Initialize the View Manager
    view_manager = ViewManager(root)

    # Add views to the manager
    view_manager.add_view("LoginView", LoginView)
    view_manager.add_view("DashboardView", DashboardView)
    view_manager.add_view("ScraperView", ScraperView)
    view_manager.add_view("JobListingsView", JobListingsView)  # Add JobListingsView

    # Show the initial view (Login view)
    view_manager.show_view("LoginView")

    # Start the CustomTkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()
