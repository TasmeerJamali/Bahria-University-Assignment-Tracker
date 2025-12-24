"""
GUI Module
Tkinter-based user interface for BU Assignment Tracker.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
from datetime import datetime


class SetupWindow:
    """First-run setup window for credential collection."""
    
    INSTITUTES = [
        "Karachi Campus",
        "Islamabad E-8 Campus",
        "Lahore Campus",
        "Health Sciences Campus"
    ]
    
    def __init__(self, on_save_callback):
        self.on_save_callback = on_save_callback
        self.root = tk.Tk()
        self.root.title("BU Assignment Tracker - Setup")
        self.root.geometry("450x520")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 450) // 2
        y = (self.root.winfo_screenheight() - 520) // 2
        self.root.geometry(f"450x520+{x}+{y}")
        
        # Bind Enter key to save
        self.root.bind('<Return>', lambda e: self._save_credentials())
        
        self._create_widgets()
        
    def _create_widgets(self):
        # Title
        title_frame = tk.Frame(self.root, bg="#1a1a2e")
        title_frame.pack(pady=20)
        
        tk.Label(
            title_frame,
            text="🎓",
            font=("Segoe UI Emoji", 32),
            bg="#1a1a2e",
            fg="white"
        ).pack()
        
        tk.Label(
            title_frame,
            text="Bahria University",
            font=("Segoe UI", 18, "bold"),
            bg="#1a1a2e",
            fg="#4ecca3"
        ).pack()
        
        tk.Label(
            title_frame,
            text="Assignment Tracker",
            font=("Segoe UI", 12),
            bg="#1a1a2e",
            fg="#a0a0a0"
        ).pack()
        
        # Form
        form_frame = tk.Frame(self.root, bg="#1a1a2e")
        form_frame.pack(pady=20, padx=40, fill="x")
        
        # Enrollment
        tk.Label(
            form_frame,
            text="Enrollment Number",
            font=("Segoe UI", 10),
            bg="#1a1a2e",
            fg="white"
        ).pack(anchor="w")
        
        self.enrollment_var = tk.StringVar()
        enrollment_entry = tk.Entry(
            form_frame,
            textvariable=self.enrollment_var,
            font=("Segoe UI", 11),
            bg="#16213e",
            fg="white",
            insertbackground="white",
            relief="flat",
            bd=0
        )
        enrollment_entry.pack(fill="x", pady=(5, 15), ipady=8)
        
        # Password
        tk.Label(
            form_frame,
            text="Password",
            font=("Segoe UI", 10),
            bg="#1a1a2e",
            fg="white"
        ).pack(anchor="w")
        
        self.password_var = tk.StringVar()
        password_entry = tk.Entry(
            form_frame,
            textvariable=self.password_var,
            font=("Segoe UI", 11),
            bg="#16213e",
            fg="white",
            insertbackground="white",
            relief="flat",
            show="•",
            bd=0
        )
        password_entry.pack(fill="x", pady=(5, 15), ipady=8)
        
        # Institute
        tk.Label(
            form_frame,
            text="Institute",
            font=("Segoe UI", 10),
            bg="#1a1a2e",
            fg="white"
        ).pack(anchor="w")
        
        self.institute_var = tk.StringVar(value=self.INSTITUTES[0])
        institute_combo = ttk.Combobox(
            form_frame,
            textvariable=self.institute_var,
            values=self.INSTITUTES,
            state="readonly",
            font=("Segoe UI", 10)
        )
        institute_combo.pack(fill="x", pady=(5, 20))
        
        # Save button
        save_btn = tk.Button(
            form_frame,
            text="Save & Continue",
            font=("Segoe UI", 11, "bold"),
            bg="#4ecca3",
            fg="#1a1a2e",
            activebackground="#3db892",
            relief="flat",
            cursor="hand2",
            command=self._save_credentials
        )
        save_btn.pack(fill="x", ipady=10)
        
    def _save_credentials(self):
        enrollment = self.enrollment_var.get().strip()
        password = self.password_var.get().strip()
        institute = self.institute_var.get()
        
        if not enrollment:
            messagebox.showerror("Error", "Please enter your enrollment number")
            return
        if not password:
            messagebox.showerror("Error", "Please enter your password")
            return
            
        self.on_save_callback(enrollment, password, institute)
        self.root.destroy()
        
    def run(self):
        self.root.mainloop()


class MainWindow:
    """Main dashboard window showing assignments."""
    
    # CMS-style Light Professional Theme
    COLORS = {
        "bg": "#f5f5f5",              # Light gray background
        "card_bg": "#ffffff",          # White cards
        "urgent": "#dc3545",           # Red for urgent/overdue
        "soon": "#fd7e14",             # Orange for due soon
        "upcoming": "#28a745",         # Green for upcoming
        "submitted": "#6c757d",        # Gray for completed
        "text": "#212529",             # Dark text
        "text_muted": "#6c757d",       # Muted gray text
        "accent": "#0d6efd",           # Blue accent (like CMS)
        "header_bg": "#343a40",        # Dark header
        "border": "#dee2e6"            # Light border
    }
    
    def __init__(self, credentials, automation_class):
        self.credentials = credentials
        self.automation_class = automation_class
        self.assignments = []
        
        self.root = tk.Tk()
        self.root.title("BU Assignment Tracker")
        self.root.geometry("550x700")
        self.root.configure(bg=self.COLORS["bg"])
        self.root.minsize(450, 500)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 550) // 2
        y = (self.root.winfo_screenheight() - 700) // 2
        self.root.geometry(f"550x700+{x}+{y}")
        
        self._create_widgets()
        
        # Start loading on launch
        self.root.after(500, self._start_refresh)
        
    def _create_widgets(self):
        # Header
        header = tk.Frame(self.root, bg=self.COLORS["bg"])
        header.pack(fill="x", padx=20, pady=15)
        
        tk.Label(
            header,
            text="🎓 Bahria University Assignment Tracker",
            font=("Segoe UI", 14, "bold"),
            bg=self.COLORS["bg"],
            fg=self.COLORS["accent"]
        ).pack(side="left")
        
        # Last updated
        self.last_updated_label = tk.Label(
            header,
            text="",
            font=("Segoe UI", 9),
            bg=self.COLORS["bg"],
            fg=self.COLORS["text_muted"]
        )
        self.last_updated_label.pack(side="right")
        
        # Status bar
        self.status_frame = tk.Frame(self.root, bg=self.COLORS["card_bg"])
        self.status_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Initializing...",
            font=("Segoe UI", 10),
            bg=self.COLORS["card_bg"],
            fg=self.COLORS["text_muted"],
            pady=8
        )
        self.status_label.pack()
        
        # Scrollable content area
        self.canvas = tk.Canvas(
            self.root,
            bg=self.COLORS["bg"],
            highlightthickness=0
        )
        self.scrollbar = ttk.Scrollbar(
            self.root,
            orient="vertical",
            command=self.canvas.yview
        )
        
        self.content_frame = tk.Frame(self.canvas, bg=self.COLORS["bg"])
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True, padx=20)
        
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.content_frame,
            anchor="nw"
        )
        
        self.content_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Bottom buttons
        btn_frame = tk.Frame(self.root, bg=self.COLORS["bg"])
        btn_frame.pack(fill="x", padx=20, pady=15)
        
        self.refresh_btn = tk.Button(
            btn_frame,
            text="🔄 Refresh",
            font=("Segoe UI", 10),
            bg=self.COLORS["accent"],
            fg=self.COLORS["bg"],
            activebackground="#3db892",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            command=self._start_refresh
        )
        self.refresh_btn.pack(side="left", padx=(0, 10))
        
        tk.Button(
            btn_frame,
            text="🌐 Open LMS",
            font=("Segoe UI", 10),
            bg=self.COLORS["card_bg"],
            fg=self.COLORS["text"],
            activebackground="#1e2a47",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            command=self._open_lms
        ).pack(side="left", padx=(0, 10))
        
        tk.Button(
            btn_frame,
            text="⚙️ Settings",
            font=("Segoe UI", 10),
            bg=self.COLORS["card_bg"],
            fg=self.COLORS["text"],
            activebackground="#1e2a47",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            command=self._open_settings
        ).pack(side="left", padx=(0, 10))
        
        # Copy Summary button
        tk.Button(
            btn_frame,
            text="📋 Copy Summary",
            font=("Segoe UI", 10),
            bg=self.COLORS["card_bg"],
            fg=self.COLORS["text"],
            activebackground="#1e2a47",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            command=self._copy_summary
        ).pack(side="left", padx=(0, 10))
        
        # Enable Notifications button (auto-sync + manual sync)
        tk.Button(
            btn_frame,
            text="📱 Enable Notifications",
            font=("Segoe UI", 10, "bold"),
            bg="#10b981",  # Green
            fg="white",
            activebackground="#059669",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            command=self._enable_notifications
        ).pack(side="left")
        
    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
    def _update_status(self, message):
        """Update status label from any thread."""
        self.root.after(0, lambda: self.status_label.configure(text=message))
        
    def _start_refresh(self):
        """Start the refresh process in background."""
        self.refresh_btn.configure(state="disabled")
        self._update_status("Starting browser automation...")
        
        thread = threading.Thread(target=self._fetch_assignments, daemon=True)
        thread.start()
        
    def _fetch_assignments(self):
        """Fetch assignments in background thread."""
        automation = None
        error_message = None
        try:
            automation = self.automation_class(
                headless=False,
                progress_callback=self._update_status
            )
            
            automation.start_browser()
            automation.login_to_cms(
                self.credentials["enrollment"],
                self.credentials["password"],
                self.credentials["institute"]
            )
            automation.navigate_to_lms()
            assignments = automation.scrape_assignments()
            
            self.assignments = assignments
            self.root.after(0, self._display_assignments)
            
        except Exception as e:
            error_message = str(e)
            self.root.after(0, lambda msg=error_message: self._show_error(msg))
        finally:
            if automation:
                automation.close()
            self.root.after(0, lambda: self.refresh_btn.configure(state="normal"))
            
    def _show_error(self, message):
        """Show error message."""
        self._update_status(f"❌ Error: {message}")
        messagebox.showerror("Error", message)
        
    def _display_assignments(self):
        """Display assignments in the UI."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Update timestamp
        now = datetime.now().strftime("%b %d, %Y %I:%M %p")
        self.last_updated_label.configure(text=f"Updated: {now}")
        
        # Categorize assignments
        pending = [a for a in self.assignments if a["status"] != "Submitted"]
        submitted = [a for a in self.assignments if a["status"] == "Submitted"]
        
        # Sort pending by days left
        pending.sort(key=lambda x: x["days_left"] if x["days_left"] is not None else 999)
        
        # Update status
        self._update_status(f"📚 {len(pending)} pending, {len(submitted)} submitted")
        
        if not pending:
            # No pending assignments
            self._create_empty_state()
        else:
            # Show pending assignments by urgency - FIXED: overdue separate from urgent
            overdue = [a for a in pending if a["days_left"] is not None and a["days_left"] < 0]
            urgent = [a for a in pending if a["days_left"] is not None and 0 <= a["days_left"] <= 3]
            soon = [a for a in pending if a["days_left"] is not None and 4 <= a["days_left"] <= 7]
            upcoming = [a for a in pending if a["days_left"] is not None and a["days_left"] > 7]
            unknown = [a for a in pending if a["days_left"] is None]
            
            if overdue:
                self._create_section("🔴 OVERDUE (Past Deadline)", overdue, self.COLORS["urgent"])
            if urgent:
                self._create_section("� URGENT (Due in 0-3 days)", urgent, self.COLORS["soon"])
            if soon:
                self._create_section("🟡 DUE SOON (4-7 days)", soon, self.COLORS["soon"])
            if upcoming:
                self._create_section("🟢 UPCOMING (8+ days)", upcoming, self.COLORS["upcoming"])
            if unknown:
                self._create_section("⚪ UNKNOWN DEADLINE", unknown, self.COLORS["text_muted"])
                
        # Submitted section (collapsible)
        if submitted:
            self._create_submitted_section(submitted)
            
    def _create_empty_state(self):
        """Show empty state when no pending assignments."""
        frame = tk.Frame(self.content_frame, bg=self.COLORS["bg"])
        frame.pack(fill="x", pady=50)
        
        tk.Label(
            frame,
            text="🎉",
            font=("Segoe UI Emoji", 48),
            bg=self.COLORS["bg"]
        ).pack()
        
        tk.Label(
            frame,
            text="No Pending Assignments!",
            font=("Segoe UI", 16, "bold"),
            bg=self.COLORS["bg"],
            fg=self.COLORS["accent"]
        ).pack(pady=10)
        
        tk.Label(
            frame,
            text="You're all caught up. Great job!",
            font=("Segoe UI", 11),
            bg=self.COLORS["bg"],
            fg=self.COLORS["text_muted"]
        ).pack()
        
    def _create_section(self, title, assignments, color):
        """Create a section with assignments."""
        section = tk.Frame(self.content_frame, bg=self.COLORS["bg"])
        section.pack(fill="x", pady=(15, 5))
        
        tk.Label(
            section,
            text=title,
            font=("Segoe UI", 11, "bold"),
            bg=self.COLORS["bg"],
            fg=color
        ).pack(anchor="w")
        
        for assignment in assignments:
            self._create_assignment_card(section, assignment, color)
            
    def _create_assignment_card(self, parent, assignment, color):
        """Create a card for a single assignment."""
        card = tk.Frame(parent, bg=self.COLORS["card_bg"])
        card.pack(fill="x", pady=5, padx=(15, 0))
        
        # Left border
        border = tk.Frame(card, bg=color, width=4)
        border.pack(side="left", fill="y")
        
        content = tk.Frame(card, bg=self.COLORS["card_bg"])
        content.pack(side="left", fill="both", expand=True, padx=15, pady=12)
        
        # Course name
        tk.Label(
            content,
            text=assignment["course"],
            font=("Segoe UI", 10),
            bg=self.COLORS["card_bg"],
            fg=self.COLORS["text_muted"]
        ).pack(anchor="w")
        
        # Assignment title
        tk.Label(
            content,
            text=f'"{assignment["title"]}"',
            font=("Segoe UI", 11, "bold"),
            bg=self.COLORS["card_bg"],
            fg=self.COLORS["text"]
        ).pack(anchor="w", pady=(2, 0))
        
        # Deadline
        deadline_text = f"Due: {assignment['deadline']}"
        if assignment["days_left"] is not None:
            if assignment["days_left"] < 0:
                deadline_text += f" ({abs(assignment['days_left'])} days ago)"
            elif assignment["days_left"] == 0:
                deadline_text += " (TODAY!)"
            elif assignment["days_left"] == 1:
                deadline_text += " (Tomorrow)"
            else:
                deadline_text += f" ({assignment['days_left']} days left)"
                
        tk.Label(
            content,
            text=deadline_text,
            font=("Segoe UI", 9),
            bg=self.COLORS["card_bg"],
            fg=color
        ).pack(anchor="w", pady=(4, 0))
        
        # Open button - opens assignment page in browser
        if assignment.get("url"):
            open_btn = tk.Label(
                content,
                text="🔗 Open in LMS",
                font=("Segoe UI", 9, "underline"),
                bg=self.COLORS["card_bg"],
                fg=self.COLORS["accent"],
                cursor="hand2"
            )
            open_btn.pack(anchor="w", pady=(6, 0))
            open_btn.bind("<Button-1>", lambda e, url=assignment["url"]: self._open_url(url))
        
    def _create_submitted_section(self, assignments):
        """Create collapsible submitted section."""
        section = tk.Frame(self.content_frame, bg=self.COLORS["bg"])
        section.pack(fill="x", pady=(20, 10))
        
        self.submitted_expanded = False
        
        header = tk.Frame(section, bg=self.COLORS["card_bg"], cursor="hand2")
        header.pack(fill="x")
        
        self.submitted_label = tk.Label(
            header,
            text=f"✅ Completed Assignments ({len(assignments)}) ▶",
            font=("Segoe UI", 10),
            bg=self.COLORS["card_bg"],
            fg=self.COLORS["submitted"],
            pady=10,
            padx=10
        )
        self.submitted_label.pack(anchor="w")
        
        self.submitted_content = tk.Frame(section, bg=self.COLORS["bg"])
        
        for assignment in assignments:
            self._create_submitted_card(self.submitted_content, assignment)
            
        header.bind("<Button-1>", self._toggle_submitted)
        self.submitted_label.bind("<Button-1>", self._toggle_submitted)
        
    def _toggle_submitted(self, event=None):
        """Toggle submitted section visibility."""
        self.submitted_expanded = not self.submitted_expanded
        
        if self.submitted_expanded:
            self.submitted_content.pack(fill="x")
            self.submitted_label.configure(
                text=self.submitted_label.cget("text").replace("▶", "▼")
            )
        else:
            self.submitted_content.pack_forget()
            self.submitted_label.configure(
                text=self.submitted_label.cget("text").replace("▼", "▶")
            )
            
    def _create_submitted_card(self, parent, assignment):
        """Create a muted card for submitted assignment."""
        card = tk.Frame(parent, bg=self.COLORS["card_bg"])
        card.pack(fill="x", pady=3, padx=(15, 0))
        
        content = tk.Frame(card, bg=self.COLORS["card_bg"])
        content.pack(fill="both", expand=True, padx=15, pady=8)
        
        tk.Label(
            content,
            text=f"✓ {assignment['course']} - {assignment['title']}",
            font=("Segoe UI", 9),
            bg=self.COLORS["card_bg"],
            fg=self.COLORS["submitted"]
        ).pack(anchor="w")
        
    def _open_lms(self):
        """Open LMS in default browser."""
        webbrowser.open("https://lms.bahria.edu.pk/Student/Dashboard.php")
    
    def _open_url(self, url):
        """Open assignment via automated login (like main scraper)."""
        # Run in background thread to not freeze UI
        def open_automated():
            try:
                self._update_status("🔐 Opening assignment (logging in)...")
                
                # Import here to avoid circular imports
                from automation import BUAutomation
                
                # Create automation instance (visible browser, don't close it)
                automation = BUAutomation(
                    headless=False,
                    progress_callback=self._update_status
                )
                
                automation.start_browser()
                automation.login_to_cms(
                    self.credentials["enrollment"],
                    self.credentials["password"],
                    self.credentials["institute"]
                )
                automation.navigate_to_lms()
                
                # Navigate to the assignment URL
                self._update_status("📄 Opening assignment page...")
                automation.driver.get(url)
                
                self._update_status("✅ Assignment opened! (Browser left open)")
                
                # Don't close the browser - leave it open for user
                # automation.close()  <-- intentionally not called
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to open: {str(e)}"))
                self._update_status("Ready")
        
        threading.Thread(target=open_automated, daemon=True).start()
        
    def _open_settings(self):
        """Open settings dialog."""
        result = messagebox.askyesno(
            "Settings",
            "Do you want to reset your saved credentials?\n\n"
            "This will delete your saved login info and you'll need to enter it again."
        )
        if result:
            from credentials import delete_credentials
            delete_credentials()
            messagebox.showinfo(
                "Settings",
                "Credentials deleted. Please restart the application."
            )
            self.root.destroy()
    
    def _copy_summary(self):
        """Copy formatted assignment summary to clipboard."""
        if not hasattr(self, 'assignments') or not self.assignments:
            messagebox.showwarning("No Data", "No assignments to export. Please refresh first.")
            return
        
        summary = self._generate_summary()
        
        # Copy to clipboard
        self.root.clipboard_clear()
        self.root.clipboard_append(summary)
        self.root.update()
        
        # Ask if user wants to save to file too
        result = messagebox.askyesno(
            "✅ Copied!",
            "Summary copied to clipboard!\n\n"
            "You can now paste it in WhatsApp, Notes, etc.\n\n"
            "Do you also want to save it as a text file?"
        )
        
        if result:
            self._save_summary_to_file(summary)
    
    def _generate_summary(self):
        """Generate formatted text summary of assignments."""
        from datetime import datetime
        
        lines = []
        lines.append("═" * 40)
        lines.append("    🎓 BU ASSIGNMENT TRACKER")
        lines.append("    📅 " + datetime.now().strftime("%B %d, %Y %I:%M %p"))
        lines.append("═" * 40)
        lines.append("")
        
        # Categorize assignments
        pending = [a for a in self.assignments if a["status"] != "Submitted"]
        submitted = [a for a in self.assignments if a["status"] == "Submitted"]
        
        overdue = [a for a in pending if a["days_left"] is not None and a["days_left"] < 0]
        urgent = [a for a in pending if a["days_left"] is not None and 0 <= a["days_left"] <= 3]
        soon = [a for a in pending if a["days_left"] is not None and 4 <= a["days_left"] <= 7]
        upcoming = [a for a in pending if a["days_left"] is not None and a["days_left"] > 7]
        
        # Summary stats
        lines.append(f"📊 SUMMARY: {len(pending)} pending, {len(submitted)} submitted")
        lines.append("")
        
        # Overdue section
        if overdue:
            lines.append("🔴 OVERDUE (Past Deadline)")
            lines.append("-" * 35)
            for a in overdue:
                lines.append(f"  ❌ {a['course']}")
                lines.append(f"     \"{a['title']}\"")
                lines.append(f"     Due: {a['deadline']} ({abs(a['days_left'])} days ago)")
                lines.append("")
        
        # Urgent section
        if urgent:
            lines.append("🟠 URGENT (Due in 0-3 days)")
            lines.append("-" * 35)
            for a in urgent:
                if a['days_left'] == 0:
                    days_text = "TODAY!"
                elif a['days_left'] == 1:
                    days_text = "Tomorrow"
                else:
                    days_text = f"{a['days_left']} days left"
                lines.append(f"  ⚠️ {a['course']}")
                lines.append(f"     \"{a['title']}\"")
                lines.append(f"     Due: {a['deadline']} ({days_text})")
                lines.append("")
        
        # Due soon section
        if soon:
            lines.append("🟡 DUE SOON (4-7 days)")
            lines.append("-" * 35)
            for a in soon:
                lines.append(f"  📌 {a['course']}")
                lines.append(f"     \"{a['title']}\"")
                lines.append(f"     Due: {a['deadline']} ({a['days_left']} days left)")
                lines.append("")
        
        # Upcoming section
        if upcoming:
            lines.append("🟢 UPCOMING (8+ days)")
            lines.append("-" * 35)
            for a in upcoming:
                lines.append(f"  ✓ {a['course']}")
                lines.append(f"     \"{a['title']}\"")
                lines.append(f"     Due: {a['deadline']} ({a['days_left']} days left)")
                lines.append("")
        
        # Completed section
        if submitted:
            lines.append(f"✅ COMPLETED ({len(submitted)} assignments)")
            lines.append("-" * 35)
            for a in submitted:
                lines.append(f"  ✓ {a['course']} - {a['title']}")
            lines.append("")
        
        # Footer
        lines.append("═" * 40)
        lines.append("Generated by BU Assignment Tracker")
        lines.append("github.com/TasmeerJamali/Bahria-University-Assignment-Tracker")
        lines.append("═" * 40)
        
        return "\n".join(lines)
    
    def _save_summary_to_file(self, summary):
        """Save summary to a text file."""
        from datetime import datetime
        from tkinter import filedialog
        
        # Generate default filename
        default_name = f"BU_Assignments_{datetime.now().strftime('%Y-%m-%d_%H%M')}.txt"
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_name,
            title="Save Assignment Summary"
        )
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(summary)
            messagebox.showinfo("Saved!", f"Summary saved to:\n{filepath}")
    
    def _sync_to_cloud(self):
        """Sync assignments to cloud for phone notifications."""
        import requests
        import json
        
        if not self.assignments:
            messagebox.showwarning(
                "No Data",
                "No assignments to sync. Please fetch assignments first."
            )
            return
        
        # Get enrollment from credentials
        try:
            with open("credentials.json", "r") as f:
                creds = json.load(f)
            enrollment = creds.get("enrollment", "")
        except Exception:
            messagebox.showerror(
                "Error",
                "Could not read enrollment. Please check credentials."
            )
            return
        
        if not enrollment:
            messagebox.showerror("Error", "Enrollment number not found.")
            return
        
        # Prepare data for cloud
        assignments_data = []
        for a in self.assignments:
            assignments_data.append({
                "course": a.get("course", "Unknown"),
                "title": a.get("title", ""),
                "deadline": a.get("deadline", ""),
                "days_left": a.get("days_left"),
                "status": a.get("status", "")
            })
        
        payload = {
            "enrollment": enrollment,
            "assignments": assignments_data
        }
        
        # Send to cloud API
        CLOUD_API = "https://buassignmenttracker.pythonanywhere.com/api/sync"
        
        try:
            self._update_status("Syncing to cloud...")
            
            response = requests.post(
                CLOUD_API,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                topic = result.get("topic", f"bu-assignments-{enrollment.lower()}")
                urgent = result.get("urgent_count", 0)
                
                messagebox.showinfo(
                    "Synced!",
                    f"✅ {len(assignments_data)} assignments synced to cloud!\n\n"
                    f"📱 To receive phone notifications:\n"
                    f"1. Install 'ntfy' app (Play Store/App Store)\n"
                    f"2. Subscribe to topic:\n   {topic}\n\n"
                    f"⚠️ Urgent assignments: {urgent}"
                )
                self._update_status(f"Synced! Topic: {topic}")
            else:
                messagebox.showerror(
                    "Sync Failed",
                    f"Server returned error: {response.status_code}\n{response.text}"
                )
                self._update_status("Sync failed")
                
        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Connection Error",
                "Could not connect to cloud server.\n"
                "The server may be starting up (try again in 30 seconds)."
            )
            self._update_status("Connection failed")
        except Exception as e:
            messagebox.showerror("Sync Error", f"Error syncing: {str(e)}")
            self._update_status("Sync error")
    
    def _enable_notifications(self):
        """Enable automatic cloud notifications for this student."""
        import requests
        import json
        
        # Get credentials
        try:
            with open("credentials.json", "r") as f:
                creds = json.load(f)
            enrollment = creds.get("enrollment", "")
            password = creds.get("password", "")
            institute = creds.get("institute", "Karachi Campus")
        except Exception:
            messagebox.showerror(
                "Error",
                "Could not read credentials. Please check settings."
            )
            return
        
        if not enrollment or not password:
            messagebox.showerror("Error", "Credentials not found.")
            return
        
        # API endpoints
        REGISTER_API = "https://buassignmenttracker.pythonanywhere.com/api/register"
        SYNC_API = "https://buassignmenttracker.pythonanywhere.com/api/sync"
        
        try:
            self._update_status("Enabling notifications...")
            
            # Step 1: Register for auto-sync
            register_response = requests.post(
                REGISTER_API,
                json={
                    "enrollment": enrollment,
                    "password": password,
                    "institute": institute
                },
                timeout=30
            )
            
            if register_response.status_code != 200:
                messagebox.showerror(
                    "Registration Failed",
                    f"Could not register: {register_response.text}"
                )
                return
            
            topic = f"bu-assignments-{enrollment.lower()}"
            
            # Step 2: Also sync current assignments if available
            if self.assignments:
                assignments_data = []
                for a in self.assignments:
                    assignments_data.append({
                        "course": a.get("course", "Unknown"),
                        "title": a.get("title", ""),
                        "deadline": a.get("deadline", ""),
                        "days_left": a.get("days_left"),
                        "status": a.get("status", "")
                    })
                
                requests.post(
                    SYNC_API,
                    json={"enrollment": enrollment, "assignments": assignments_data},
                    timeout=30
                )
            
            # Show success with instructions
            messagebox.showinfo(
                "🎉 Notifications Enabled!",
                f"You're all set for automatic notifications!\n\n"
                f"📱 To receive notifications on your phone:\n\n"
                f"1. Install 'ntfy' app (Play Store / App Store)\n"
                f"2. Open app → Tap '+'\n"
                f"3. Subscribe to topic:\n"
                f"   {topic}\n\n"
                f"📅 Schedule:\n"
                f"• 6 AM - Cloud scrapes your LMS\n"
                f"• 8 AM, 2 PM, 8 PM - Notifications sent\n\n"
                f"✨ Works even when your laptop is OFF!"
            )
            
            self._update_status(f"Notifications enabled! Topic: {topic}")
            
        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Connection Error",
                "Could not connect to cloud server.\nPlease try again."
            )
            self._update_status("Connection failed")
        except Exception as e:
            messagebox.showerror("Error", f"Error enabling notifications: {str(e)}")
            self._update_status("Error")
            
    def run(self):
        self.root.mainloop()
