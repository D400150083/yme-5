# YME v5 — YouTube Metadata Extractor

Professional desktop tool for extracting YouTube metadata with a modern GUI.

![YME Logo](yme.png)

## Overview

**YME v5** is a Python + CustomTkinter desktop application for:

- extracting metadata from a single YouTube video,
- scraping metadata in batch mode from multiple video links,
- extracting channel profile details,
- fetching latest channel videos with user-defined count,
- exporting results to JSON/CSV,
- downloading HD thumbnail for single-video mode.

The app uses **YouTube Data API v3**.

---

## Main Features

### 1) Video Metadata Tab

- **Single Mode (1 Video)**
  - Input one YouTube video URL
  - Extract channel + video metadata
  - Download video thumbnail (HD if available)

- **Batch Mode (Multi-Link)**
  - Input multiple URLs (1 per line)
  - Auto-filter valid links
  - Remove duplicate video IDs
  - Display summarized batch result in output panel

### 2) Channel Detail Tab

- Supports channel inputs:
  - `https://www.youtube.com/channel/UC...`
  - `https://www.youtube.com/@handle`
  - `https://www.youtube.com/c/...`
  - `https://www.youtube.com/user/...`
  - channel name query
- User selects latest video count manually (`0-50`)
- Extracts:
  - channel profile metadata
  - latest N videos (title, views, likes, comments, upload time)

### 3) Export

- Export result to:
  - **JSON**
  - **CSV**

### 4) API Key Input (UI)

- API key can be entered manually in app UI
- Input is masked for privacy
- API client can be re-initialized from UI button

---

## Extracted Data Fields

### Video Data

- Channel name, channel ID, channel creation time, country
- Subscriber count, total channel videos
- Video title, video ID, upload time
- Views, likes, comments
- Thumbnail URL
- Tags
- Description

### Channel Data

- Channel title, channel ID, custom URL
- Channel creation time, country
- Subscribers, total channel views, total channel videos
- Channel thumbnail URL
- Channel description
- Latest videos list:
  - title
  - video ID
  - upload time (WIB)
  - views
  - likes
  - comments
  - video URL
  - thumbnail URL

---

## Tech Stack

- Python
- CustomTkinter
- Tkinter
- YouTube Data API v3 (`google-api-python-client`)
- PyInstaller (for `.exe` build)

---

## Project Structure

```text
.
├─ scrap v5.py          # Main application source
├─ dist/
│  └─ YME v5.exe        # Built Windows executable
├─ yme.png              # Main logo asset
├─ yme_icon.png         # Runtime icon asset
├─ yme.ico              # Windows executable icon
└─ README.md
```

---

## Setup (Run from Source)

### 1) Create virtual environment (recommended)

```bash
python -m venv .venv
```

### 2) Activate venv

**Windows (cmd):**

```bash
.venv\Scripts\activate
```

### 3) Install dependencies

```bash
pip install customtkinter google-api-python-client
```

### 4) Run app

```bash
python "scrap v5.py"
```

---

## Run from EXE

Use prebuilt executable:

- `dist/YME v5.exe`

No Python installation required on target machine.

---

## Build EXE (PyInstaller)

```bash
pyinstaller --noconfirm --clean --windowed --onefile --name "YME v5" --icon "yme.ico" --add-data "yme_icon.png;." --add-data "yme.png;." "scrap v5.py"
```

---

## API Key Notes

- Generate API key from Google Cloud Console
- Enable **YouTube Data API v3** for project
- Input key in app UI (top section)
- Do **not** commit real API keys into public repositories

---

## Limitations

- API quota applies (daily limits from Google)
- Some fields may be unavailable for certain videos/channels (e.g., likes/comments hidden)
- Batch/channel requests depend on network stability and API response health

---

## Troubleshooting

- **`gh` command not found**: install GitHub CLI and ensure PATH is updated
- **Icon not updating in taskbar**: unpin old shortcut, open new EXE, pin again
- **No data returned**: verify API key validity, API quota, and URL format

---

## Disclaimer

This tool is intended for educational and operational metadata analysis use-cases. Ensure compliance with YouTube Terms of Service and applicable platform/API policies.
