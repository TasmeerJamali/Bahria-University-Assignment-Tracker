"""
BU Assignment Tracker
Main entry point for the application.

Automates login to Bahria University CMS/LMS and displays pending assignments.
"""

import sys
import os

# Ensure we can find modules when running as exe
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

from credentials import credentials_exist, load_credentials, save_credentials
from gui import SetupWindow, MainWindow
from automation import BUAutomation


def main():
    """Main application entry point."""
    
    if not credentials_exist():
        # First run - show setup
        def on_save(enrollment, password, institute):
            save_credentials(enrollment, password, institute)
            show_main_window()
            
        setup = SetupWindow(on_save)
        setup.run()
    else:
        show_main_window()


def show_main_window():
    """Show the main dashboard window."""
    credentials = load_credentials()
    
    if not credentials:
        # Credentials corrupted, show setup again
        def on_save(enrollment, password, institute):
            save_credentials(enrollment, password, institute)
            show_main_window()
            
        setup = SetupWindow(on_save)
        setup.run()
        return
        
    app = MainWindow(credentials, BUAutomation)
    app.run()


if __name__ == "__main__":
    main()
