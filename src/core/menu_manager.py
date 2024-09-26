import tkinter as tk  # Import standard tkinter for Menu

def create_menu(root, view_manager):
    """
    Create a menu bar for the application after successful login.
    
    Args:
    - root: The root window of the Tkinter application.
    - view_manager: The ViewManager instance to manage view switching.
    """
    menu_bar = tk.Menu(root)  # Use standard Tkinter Menu

    # Create the "View" menu
    view_menu = tk.Menu(menu_bar, tearoff=0)
    view_menu.add_command(label="Dashboard", command=lambda: view_manager.show_view("DashboardView"))
    view_menu.add_command(label="Scraper Management", command=lambda: view_manager.show_view("ScraperView"))

    # Add the "View" menu to the menu bar
    menu_bar.add_cascade(label="View", menu=view_menu)

    # Attach the menu bar to the root window
    root.config(menu=menu_bar)  # This configures the menu to the root window
