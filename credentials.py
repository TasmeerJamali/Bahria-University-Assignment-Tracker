"""
Credential Storage Module
Handles saving and loading user credentials from JSON file.
"""

import json
import os

CREDENTIALS_FILE = "credentials.json"


def get_credentials_path():
    """Get the path to credentials file (same directory as executable)."""
    if getattr(os.sys, 'frozen', False):
        # Running as compiled exe
        base_path = os.path.dirname(os.sys.executable)
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, CREDENTIALS_FILE)


def credentials_exist():
    """Check if credentials file exists."""
    return os.path.exists(get_credentials_path())


def load_credentials():
    """Load credentials from JSON file."""
    try:
        with open(get_credentials_path(), 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_credentials(enrollment, password, institute):
    """Save credentials to JSON file."""
    credentials = {
        "enrollment": enrollment,
        "password": password,
        "institute": institute
    }
    with open(get_credentials_path(), 'w') as f:
        json.dump(credentials, f, indent=2)
    return True


def delete_credentials():
    """Delete the credentials file."""
    path = get_credentials_path()
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
