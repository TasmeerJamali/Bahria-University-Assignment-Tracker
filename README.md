# 🎓 Bahria University Assignment Tracker

Automatic assignment tracker for Bahria University LMS with deadline alerts and turbo-speed fetching.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

- **⚡ Turbo Mode** - Fetches all courses in ~5 seconds (parallel HTTP requests)
- **🎨 Clean UI** - CMS-style light theme with color-coded deadlines
- **🔴 Smart Categorization**:
  - OVERDUE (Past deadline)
  - URGENT (Due in 0-3 days)
  - DUE SOON (4-7 days)
  - UPCOMING (8+ days)
- **💾 Save Credentials** - Enter once, use forever
- **🔄 One-Click Refresh** - Update assignments anytime

## 📥 Download

**[⬇️ Download Latest Release](https://github.com/TasmeerJamali/Bahria-University-Assignment-Tracker/releases)**

Just download `BU_Assignment_Tracker.exe` and run it!

## 🚀 How to Use

1. Download `BU_Assignment_Tracker.exe` from Releases
2. Double-click to run
3. Enter your credentials (first time only):
   - Enrollment Number (e.g., `02-132222-024`)
   - Password
   - Institute (Karachi Campus, etc.)
4. Wait for the app to fetch your assignments (~15-20 seconds)
5. View all your pending assignments with color-coded deadlines!

## 📸 Screenshots

| Setup Screen | Dashboard |
|:---:|:---:|
| First-time credential setup | Your assignments at a glance |

## 🔧 Technical Details

| Component | Technology |
|-----------|------------|
| Browser Automation | Selenium + Chrome |
| GUI Framework | Tkinter |
| HTTP Requests | Python requests |
| Parallel Processing | ThreadPoolExecutor |
| Packaging | PyInstaller |

## 🛡️ Privacy

- Your credentials are stored **locally** in `credentials.json`
- No data is sent to any external server
- Open source - verify the code yourself!

## 🏫 Supported Campuses

- ✅ Karachi Campus
- ✅ Islamabad E-8 Campus
- ✅ Lahore Campus
- ✅ Health Sciences Campus

## 📋 Requirements (for running from source)

```bash
pip install -r requirements.txt
python main.py
```

## 📜 License

MIT License - Feel free to use, modify, and share!

---

Made with ❤️ for Bahria University students
