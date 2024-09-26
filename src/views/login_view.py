import customtkinter as ctk
from tkinter import messagebox
from core.menu_manager import create_menu  # Correct import from core.menu_manager

class LoginView(ctk.CTkFrame):
    """Login View Frame"""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(fg_color="#2e2e2e")  # Dark background

        # Create Login Form
        self.create_login_form()

    def create_login_form(self):
        """Create the login form UI elements."""
        # Title Label
        title_label = ctk.CTkLabel(self, text="Admin Login", font=("Helvetica", 24, "bold"), text_color="white")
        title_label.pack(pady=(50, 20))  # Padding from top

        # Username Entry
        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username", width=300)
        self.username_entry.pack(pady=(10, 10))

        # Password Entry
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=300)
        self.password_entry.pack(pady=(10, 10))

        # Login Button
        login_button = ctk.CTkButton(self, text="Login", command=self.check_login, fg_color="#1a73e8", text_color="white", width=200)
        login_button.pack(pady=(20, 10))

    def check_login(self):
        """Check the login credentials."""
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Static login check
        if username == "Admin" and password == "1234":
            messagebox.showinfo("Login Successful", "Welcome, Admin!")
            self.controller.show_view("DashboardView")  # Navigate to the dashboard

            # Create the menu bar dynamically after login
            create_menu(self.controller.root, self.controller)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
