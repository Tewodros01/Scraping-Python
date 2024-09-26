# src/views/dashboard_view.py
import tkinter as tk
from tkinter import ttk

class DashboardView(tk.Frame):
    """Dashboard view to display job scraping results and options."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Define colors and styles
        bg_color = "#3F6BAA"
        fg_color = "#E1FFFF"
        frame_styles = {"relief": "groove", "bd": 3, "bg": bg_color}

        # Main container
        main_frame = tk.Frame(self, bg=bg_color)
        main_frame.pack(fill="both", expand=True)

        # Top navigation bar
        top_frame = tk.Frame(main_frame, bg=bg_color, height=50)
        top_frame.pack(side="top", fill="x")

        title_label = tk.Label(top_frame, text="Dashboard", font=("Trebuchet MS Bold", 16), bg=bg_color, fg=fg_color)
        title_label.pack(side="left", padx=20, pady=10)

        logout_button = ttk.Button(top_frame, text="Logout", command=lambda: controller.show_view("LoginView"))
        logout_button.pack(side="right", padx=20, pady=10)

        # Left sidebar
        sidebar_frame = tk.Frame(main_frame, **frame_styles, width=200)
        sidebar_frame.pack(side="left", fill="y")

        ttk.Button(sidebar_frame, text="Home", command=self.home_action).pack(pady=10, padx=10, fill="x")
        ttk.Button(sidebar_frame, text="Scraping", command=self.scraping_action).pack(pady=10, padx=10, fill="x")
        ttk.Button(sidebar_frame, text="Settings", command=self.settings_action).pack(pady=10, padx=10, fill="x")

        # Main content area
        content_frame = tk.Frame(main_frame, bg=fg_color)
        content_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Add widgets to content frame
        label = ttk.Label(content_frame, text="Welcome to the Dashboard", font=("Helvetica", 16))
        label.pack(pady=20)

        # Example Treeview (table) for displaying data
        treeview_frame = tk.Frame(content_frame)
        treeview_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_treeview(treeview_frame)

        # Footer
        footer_frame = tk.Frame(main_frame, bg=bg_color, height=30)
        footer_frame.pack(side="bottom", fill="x")

        footer_label = tk.Label(footer_frame, text="© 2024 Job Scraper Admin Panel", bg=bg_color, fg=fg_color)
        footer_label.pack(pady=5)

    def create_treeview(self, parent):
        """Create a Treeview widget to display job scraping data."""
        columns = ("Job Title", "Company", "Location", "Date Posted")
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        tree.heading("Job Title", text="Job Title")
        tree.heading("Company", text="Company")
        tree.heading("Location", text="Location")
        tree.heading("Date Posted", text="Date Posted")

        # Set column widths
        tree.column("Job Title", width=200)
        tree.column("Company", width=150)
        tree.column("Location", width=100)
        tree.column("Date Posted", width=100)

        # Example data (Replace this with actual data loading logic)
        example_data = [
            ("Software Engineer", "TechCorp", "New York, NY", "2024-09-01"),
            ("Data Scientist", "DataWorks", "San Francisco, CA", "2024-08-29"),
            ("Web Developer", "Web Solutions", "Remote", "2024-08-30"),
        ]

        for row in example_data:
            tree.insert("", "end", values=row)

        tree.pack(fill="both", expand=True)

    # Placeholder methods for sidebar buttons
    def home_action(self):
        """Action for Home button."""
        tk.messagebox.showinfo("Information", "Home clicked!")

    def scraping_action(self):
        """Action for Scraping button."""
        tk.messagebox.showinfo("Information", "Scraping clicked!")

    def settings_action(self):
        """Action for Settings button."""
        tk.messagebox.showinfo("Information", "Settings clicked!")
