"""
Flask Web API for BU Assignment Tracker
Receives assignment data from desktop apps and stores for notifications.
"""

from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Data storage file
DATA_FILE = "/home/buassignmenttracker/bu-notifications-cloud/students_data.json"


def load_data():
    """Load students data from JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"students": {}}


def save_data(data):
    """Save students data to JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


@app.route('/')
def home():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "BU Assignment Tracker Cloud",
        "version": "1.0.0"
    })


@app.route('/api/sync', methods=['POST'])
def sync_assignments():
    """
    Receive and store assignments from desktop app.
    
    Expected JSON body:
    {
        "enrollment": "02-132222-024",
        "assignments": [
            {"course": "...", "title": "...", "deadline": "...", "days_left": 3, "status": "..."},
            ...
        ]
    }
    """
    try:
        payload = request.get_json()
        
        if not payload:
            return jsonify({"error": "No data provided"}), 400
        
        enrollment = payload.get("enrollment")
        assignments = payload.get("assignments", [])
        
        if not enrollment:
            return jsonify({"error": "Enrollment required"}), 400
        
        # Load existing data
        data = load_data()
        
        # Store/update student data
        data["students"][enrollment] = {
            "enrollment": enrollment,
            "assignments": assignments,
            "last_synced": datetime.now().isoformat(),
            "notification_enabled": True
        }
        
        # Save
        save_data(data)
        
        # Count urgent assignments
        urgent = len([a for a in assignments if a.get("days_left", 99) <= 3 and a.get("status", "").lower() != "submitted"])
        
        return jsonify({
            "success": True,
            "message": f"Synced {len(assignments)} assignments",
            "urgent_count": urgent,
            "topic": f"bu-assignments-{enrollment.lower()}"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    """
    Register a student for notifications.
    
    Expected JSON body:
    {
        "enrollment": "02-132222-024"
    }
    """
    try:
        payload = request.get_json()
        enrollment = payload.get("enrollment")
        
        if not enrollment:
            return jsonify({"error": "Enrollment required"}), 400
        
        data = load_data()
        
        if enrollment not in data["students"]:
            data["students"][enrollment] = {
                "enrollment": enrollment,
                "assignments": [],
                "last_synced": None,
                "notification_enabled": True
            }
            save_data(data)
        
        topic = f"bu-assignments-{enrollment.lower()}"
        
        return jsonify({
            "success": True,
            "topic": topic,
            "message": f"Subscribe to '{topic}' in the ntfy app to receive notifications"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/students', methods=['GET'])
def list_students():
    """List all registered students (admin only)."""
    data = load_data()
    return jsonify({
        "count": len(data["students"]),
        "students": list(data["students"].keys())
    })


@app.route('/api/register', methods=['POST'])
def register_autosync():
    """
    Register a student for automatic cloud scraping.
    
    Expected JSON body:
    {
        "enrollment": "02-132222-024",
        "password": "encrypted_password",
        "institute": "Karachi Campus"
    }
    """
    import hashlib
    import base64
    
    try:
        payload = request.get_json()
        enrollment = payload.get("enrollment")
        password = payload.get("password")
        institute = payload.get("institute", "Karachi Campus")
        
        if not enrollment or not password:
            return jsonify({"error": "Enrollment and password required"}), 400
        
        data = load_data()
        
        # Simple encryption (XOR with key) - use proper encryption in production
        key = "bu-tracker-2024"
        encrypted = base64.b64encode(
            bytes([ord(c) ^ ord(key[i % len(key)]) for i, c in enumerate(password)])
        ).decode()
        
        # Update or create student entry
        if enrollment not in data["students"]:
            data["students"][enrollment] = {"enrollment": enrollment, "assignments": []}
        
        data["students"][enrollment]["encrypted_password"] = encrypted
        data["students"][enrollment]["institute"] = institute
        data["students"][enrollment]["auto_sync"] = True
        data["students"][enrollment]["registered_at"] = datetime.now().isoformat()
        
        save_data(data)
        
        topic = f"bu-assignments-{enrollment.lower()}"
        
        return jsonify({
            "success": True,
            "message": "Registered for auto-sync. Cloud will scrape your LMS daily at 6 AM.",
            "topic": topic
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/students/autosync', methods=['GET'])
def get_autosync_students():
    """
    Get list of students with auto-sync enabled (for cloud scraper).
    Returns decrypted credentials.
    PROTECTED: Requires API key for security.
    """
    import base64
    
    # Security: Require API key
    API_KEY = "bu-tracker-secret-2024"  # This should match GitHub Actions secret
    provided_key = request.args.get('key') or request.headers.get('X-API-Key')
    
    if provided_key != API_KEY:
        return jsonify({"error": "Unauthorized. API key required."}), 401
    
    try:
        data = load_data()
        students = []
        key = "bu-tracker-2024"
        
        for enrollment, student in data.get("students", {}).items():
            if student.get("auto_sync"):
                encrypted = student.get("encrypted_password", "")
                
                # Decrypt password
                try:
                    decoded = base64.b64decode(encrypted)
                    password = "".join([chr(b ^ ord(key[i % len(key)])) for i, b in enumerate(decoded)])
                except:
                    password = ""
                
                if password:
                    students.append({
                        "enrollment": enrollment,
                        "password": password,
                        "institute": student.get("institute", "Karachi Campus")
                    })
        
        return jsonify({"students": students, "count": len(students)})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/trigger', methods=['POST'])
def trigger_notifications():
    """
    Trigger notifications for all students with urgent assignments.
    Called by GitHub Actions scheduler.
    
    Optional JSON body:
    {
        "secret": "your-secret-key"  # For basic auth (optional)
    }
    """
    import requests
    from urllib.parse import quote
    
    results = {"sent": 0, "skipped": 0, "errors": 0, "details": []}
    
    try:
        data = load_data()
        students = data.get("students", {})
        
        for enrollment, student in students.items():
            assignments = student.get("assignments", [])
            
            # Filter urgent assignments
            urgent = []
            for a in assignments:
                days = a.get("days_left")
                status = a.get("status", "")
                if days is not None and days <= 3 and status.lower() != "submitted":
                    urgent.append(a)
            
            if not urgent:
                # Send "All Clear" notification
                topic = f"bu-assignments-{enrollment.lower()}"
                all_clear_msg = (
                    "🎉 All Clear!\n\n"
                    "No urgent assignments today.\n"
                    "Keep up the great work!\n\n"
                    "✅ All assignments are either:\n"
                    "• Already submitted, or\n"
                    "• Due in 4+ days"
                )
                try:
                    response = requests.post(
                        f"https://ntfy.sh/{topic}",
                        data=all_clear_msg.encode('utf-8'),
                        headers={
                            "Title": quote("BU Assignment Tracker", safe=''),
                            "Priority": "2",
                            "Tags": "white_check_mark,tada"
                        },
                        timeout=10
                    )
                    if response.status_code == 200:
                        results["sent"] += 1
                        results["details"].append({"enrollment": enrollment, "status": "all_clear"})
                    else:
                        results["skipped"] += 1
                        results["details"].append({"enrollment": enrollment, "status": "skipped", "reason": "send failed"})
                except:
                    results["skipped"] += 1
                    results["details"].append({"enrollment": enrollment, "status": "skipped", "reason": "error"})
                continue
            
            # Build notification message
            lines = [f"WARNING: {len(urgent)} URGENT assignment(s)!", ""]
            for i, a in enumerate(urgent[:5], 1):
                days = a.get("days_left", "?")
                if days == 0:
                    time_text = "TODAY!"
                elif days == 1:
                    time_text = "Tomorrow"
                else:
                    time_text = f"{days} days left"
                lines.append(f"{i}. {a.get('course', 'Unknown')}")
                lines.append(f'   "{a.get("title", "")}"')
                lines.append(f"   Due: {time_text}")
                lines.append("")
            
            message = "\n".join(lines)
            title = "BU Assignment Reminder"
            topic = f"bu-assignments-{enrollment.lower()}"
            
            # Send via ntfy.sh
            try:
                response = requests.post(
                    f"https://ntfy.sh/{topic}",
                    data=message.encode('utf-8'),
                    headers={
                        "Title": quote(title, safe=''),
                        "Priority": "4",
                        "Tags": "school,calendar,warning"
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    results["sent"] += 1
                    results["details"].append({"enrollment": enrollment, "status": "sent", "urgent_count": len(urgent)})
                else:
                    results["errors"] += 1
                    results["details"].append({"enrollment": enrollment, "status": "error", "code": response.status_code})
            except Exception as e:
                results["errors"] += 1
                results["details"].append({"enrollment": enrollment, "status": "error", "message": str(e)})
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "results": results
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# This is for PythonAnywhere WSGI
# Don't run with app.run() on PythonAnywhere
