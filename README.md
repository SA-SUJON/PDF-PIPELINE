<div align="center">

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          ███╗   ███╗ █████╗ ███╗   ██╗ ██████╗  █████╗           ║
║          ████╗ ████║██╔══██╗████╗  ██║██╔════╝ ██╔══██╗          ║
║          ██╔████╔██║███████║██╔██╗ ██║██║  ███╗███████║          ║
║          ██║╚██╔╝██║██╔══██║██║╚██╗██║██║   ██║██╔══██║          ║
║          ██║ ╚═╝ ██║██║  ██║██║ ╚████║╚██████╔╝██║  ██║          ║
║          ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝          ║
║                                                                  ║
║                           PDF  PIPELINE                          ║
║                  Convert  ·  Organize  ·  Merge                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**A universal, GUI-powered image-to-PDF pipeline for manga, comics, and any chapter-based image collection.**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter-purple?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## Table of Contents

- [What Is This?](#what-is-this)
- [How It Works — The 3-Stage Pipeline](#how-it-works--the-3-stage-pipeline)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [How to Use](#how-to-use)
  - [Launching the App](#launching-the-app)
  - [Overview Tab — Full Pipeline](#overview-tab--full-pipeline)
  - [Stage 1 Tab — Image → PDF Convert](#stage-1-tab--image--pdf-convert)
  - [Stage 2 Tab — PDF Organizer](#stage-2-tab--pdf-organizer)
  - [Stage 3 Tab — Batch Merger](#stage-3-tab--batch-merger)
  - [Understanding the Log Panel](#understanding-the-log-panel)
- [Data Flow Diagram](#data-flow-diagram)
- [Folder & File Naming Conventions](#folder--file-naming-conventions)
- [Building a Standalone .EXE](#building-a-standalone-exe)
  - [Method 1 — PyInstaller (Recommended)](#method-1--pyinstaller-recommended)
  - [Method 2 — Nuitka (Faster Runtime)](#method-2--nuitka-faster-runtime)
  - [Method 3 — cx_Freeze](#method-3--cx_freeze)
  - [EXE Comparison Table](#exe-comparison-table)
  - [Troubleshooting the EXE Build](#troubleshooting-the-exe-build)
- [Configuration Reference](#configuration-reference)
- [Edge Cases & Known Behaviours](#edge-cases--known-behaviours)
- [FAQ](#faq)

---

## What Is This?

**Manga PDF Pipeline** is a desktop application that automates the entire workflow of converting a raw manga or comic collection — stored as image files inside chapter subfolders — into clean, organized, and merged PDF archives.

Originally built for a Private Manga And Comics archiving project for Feeding at **GOOGLE NotebookLM** cause in free tier it supports only 50 sources. So I create this script for partially bypass this limit, and now it has been refactored into a **fully universal tool** with no hardcoded paths, supporting any project, any folder structure, and any image format.

### Why This Exists

Managing hundreds of manga chapters as loose PNG/JPG files is painful. Manually converting, sorting, and merging them one by one is tedious and error-prone. This pipeline automates the entire 3-stage process in a single click, with a real-time GUI that shows exactly what is happening.

### Key Features

| Feature | Detail |
|---|---|
| 🖥️ **Modern Dark GUI** | CustomTkinter with a dark industrial terminal aesthetic |
| ⚡ **Non-Blocking Execution** | All pipeline stages run on daemon threads — UI never freezes |
| ♻️ **Idempotent Runs** | Already-converted files are auto-detected and skipped |
| 🔧 **Fully Configurable** | No hardcoded paths — every directory and parameter is user-defined |
| 🖼️ **Multi-Format Support** | PNG, JPG, JPEG, WEBP + any custom extension |
| 🗜️ **Lossless Merging** | PDF merging via `pypdf` — zero re-encoding, zero quality loss |
| 📊 **Real-Time Logging** | Colour-coded live output for every operation |
| 📦 **Compilable to EXE** | Can be packaged as a standalone Windows executable |

---

## How It Works — The 3-Stage Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PIPELINE ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐     ┌──────────────────┐     ┌─────────────┐ │
│  │   IMAGE SOURCE   │     │  INTERMEDIATE    │     │   OUTPUT    │ │
│  │                  │     │                  │     │             │ │
│  │  CHAPTER 001\    │     │  CHAPTER 001.PDF │     │  CH 001-    │ │
│  │  ├─ 001.png      │ S1  │  CHAPTER 002.PDF │ S2  │  005.PDF   │ │
│  │  ├─ 002.png      │────▶│  CHAPTER 033.PDF │────▶│            │ │
│  │  └─ 003.png      │     │  ...             │     │  CH 006-   │ │
│  │                  │     │                  │ S3  │  010.PDF   │ │
│  │  CHAPTER 002\    │     │  CHAPTER 001-    │────▶│            │ │
│  │  ├─ 001.png      │     │  005\            │     │  ...       │ │
│  │  └─ ...          │     │  CHAPTER 006-    │     │            │ │
│  └──────────────────┘     │  010\            │     └─────────────┘ │
│                           └──────────────────┘                     │
│  STAGE 1: Convert         STAGE 2: Organize   STAGE 3: Merge       │
│  Images → flat PDFs       Flat PDFs → batches Batches → 1 PDF each │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Stage 1 — Image → PDF Convert

Scans the source directory for chapter subfolders. For each subfolder, it collects all image files (sorted by filename), converts them into a single PDF using `img2pdf` (lossless, pixel-perfect), and writes one flat PDF per chapter into the output directory.

### Stage 2 — PDF Organizer

Takes the flat directory of chapter PDFs and moves them into named batch subfolders based on your configured batch size. For example, with `Batch Size = 5` and `Start = 1`, it creates:

```
CHAPTER 001 - CHAPTER 005\
CHAPTER 006 - CHAPTER 010\
CHAPTER 011 - CHAPTER 015\
...
```

### Stage 3 — Batch Merger

Iterates over each batch subfolder and losslessly merges all chapter PDFs inside into a single combined PDF using `pypdf`. The output is one PDF per batch folder, saved flat in the output directory. Zero re-encoding — every page is appended as-is at the binary level.

---

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|---|---|---|
| **OS** | Windows 8, macOS 10.14, Ubuntu 18.04 | Windows 10/11, macOS 12+, Ubuntu 22.04 |
| **Python** | 3.8 | 3.10 or 3.11 |
| **RAM** | 512 MB free | 2 GB+ for large batches |
| **Disk** | Depends on your manga collection | SSD recommended for bulk operations |
| **Display** | 900 × 660 px minimum | 1080p+ |

### Python Dependencies

| Package | Version | Purpose |
|---|---|---|
| `customtkinter` | ≥ 5.2.0 | Modern dark GUI framework |
| `img2pdf` | ≥ 0.4.4 | Lossless image-to-PDF conversion (Stage 1) |
| `pypdf` | ≥ 3.0.0 | Lossless PDF page merging (Stage 3) |

> **Note:** Stage 2 (PDF Organizer) uses only Python's built-in `os` and `shutil` modules — no extra packages required for that stage alone.

---

## Installation

### Step 1 — Verify Python

Open a terminal or Command Prompt and check your Python version:

```bash
python --version
# or on some systems:
python3 --version
```

You should see `Python 3.8.x` or higher. If Python is not installed, download it from [python.org](https://www.python.org/downloads/).

> **Windows Tip:** When installing Python, check **"Add Python to PATH"** during setup. This is critical.

---

### Step 2 — Install Dependencies

#### Option A — Using the included `requirements.txt` (Recommended)

Navigate to the folder containing the project files and run:

```bash
pip install -r requirements.txt
```

#### Option B — Manual one-liner

```bash
pip install customtkinter img2pdf pypdf
```

#### Option C — If you have multiple Python versions

```bash
python -m pip install customtkinter img2pdf pypdf
# or explicitly:
python3 -m pip install customtkinter img2pdf pypdf
```

---

### Step 3 — Verify Installation

```bash
python -c "import customtkinter, img2pdf, pypdf; print('All dependencies OK')"
```

You should see: `All dependencies OK`

---

## Project Structure

```
manga-pdf-pipeline/
│
├── manga_pipeline.py       ← Main application (single file, run this)
├── requirements.txt        ← pip dependency list
├── SETUP.txt               ← Quick-start reference
└── README.md               ← This file
```

The entire application — GUI, pipeline core, all three stages — lives in `manga_pipeline.py`. There are no submodules or config files to manage.

---

## How to Use

### Launching the App

```bash
python manga_pipeline.py
```

The GUI window opens immediately. The status indicator in the top-right corner will show:

- `● READY` (green) — All dependencies found, ready to run
- `● MISSING DEPS` (red) — One or more packages not installed; the log panel will show the exact `pip install` command needed

---

### Overview Tab — Full Pipeline

This is the primary entry point. It runs all three stages sequentially in a single click.

#### Step-by-Step

**1. Set IMAGE SOURCE**
```
The root folder containing your chapter subfolders.

Example:
  D:\SUJON\NARUTO\
  ├── CHAPTER 001\
  │   ├── 001.png
  │   ├── 002.png
  │   └── ...
  ├── CHAPTER 002\
  └── ...
```

**2. Set INTERMEDIATE**
```
The working directory. Stage 1 writes flat PDFs here.
Stage 2 then creates batch subfolders inside this same directory.

Example:  D:\SUJON\NARUTO FLAT PDF\
```

**3. Set FINAL OUTPUT**
```
Where the finished merged PDFs land.
Can be the same folder as INTERMEDIATE — the pipeline handles it cleanly.

Example:  D:\SUJON\NARUTO BATCH PDF\
```

**4. Configure Chapter Parameters**

| Field | Description | Example |
|---|---|---|
| `Batch Size` | How many chapters per merged PDF | `5` |
| `Start Chapter` | First chapter number to process | `1` |
| `End Chapter` | Last chapter number to process | `700` |
| `Skip From` | Start of skip range (already converted) | `600` |
| `Skip To` | End of skip range (already converted) | `620` |

> **Skip Range:** Chapters in the Skip From → Skip To range are ignored during Stage 1 (convert). This is for chapters you already converted manually. Set both to `0` if there's nothing to skip.

**5. Select Image Extensions**

Toggle the checkboxes for `.png`, `.jpg`, `.jpeg`, `.webp`. Use the custom field for anything else (e.g. `.bmp, .tiff`).

**6. Click `▶ RUN FULL PIPELINE`**

The progress bar and log panel activate immediately. The pipeline runs Stage 1 → 2 → 3 in sequence. The status indicator shows `● RUNNING` and each stage is clearly delineated in the log output.

---

### Stage 1 Tab — Image → PDF Convert

Run only Stage 1 independently. Useful when you've added new chapters and only need the convert step.

**Required Inputs:**
- `SOURCE` — Root folder with chapter subfolders
- `OUTPUT` — Where flat PDFs are written
- `Skip From / Skip To` — Chapters to exclude from conversion
- Image extensions — Which file types to pick up

**Output Structure:**
```
OUTPUT\
├── CHAPTER 001.PDF
├── CHAPTER 002.PDF
├── CHAPTER 003.PDF
└── ...
```

> Folders without any matching image files are logged as `[SKIP]` and do not produce an error.

---

### Stage 2 Tab — PDF Organizer

Run only Stage 2 independently. Moves flat PDFs into batch subfolders.

**Required Inputs:**
- `SOURCE` — Directory containing flat chapter PDFs
- `DESTINATION` — Where batch subfolders will be created (can equal SOURCE)
- `Batch Size`, `Start Chapter`, `End Chapter`

**Output Structure** (Batch Size = 5, Start = 1):
```
DESTINATION\
├── CHAPTER 001 - CHAPTER 005\
│   ├── CHAPTER 001.PDF
│   ├── CHAPTER 002.PDF
│   └── ...
├── CHAPTER 006 - CHAPTER 010\
└── ...
```

> Files that don't exist on disk are reported as `[WARN]` but do not crash the run — the folder is still created and other files proceed normally.

---

### Stage 3 Tab — Batch Merger

Run only Stage 3 independently. Merges each batch subfolder into one combined PDF.

**Required Inputs:**
- `SOURCE` — Directory containing the batch subfolders
- `OUTPUT` — Where merged PDFs are saved (can equal SOURCE)

**Output Structure:**
```
OUTPUT\
├── CHAPTER 001 - CHAPTER 005.PDF    ← lossless merge of 5 chapters
├── CHAPTER 006 - CHAPTER 010.PDF
└── ...
```

> Already-merged PDFs are detected and skipped (`[SKIP] Already exists`). Re-running Stage 3 on the same directory is always safe.

---

### Understanding the Log Panel

Every operation prints a colour-coded line:

| Colour | Tag | Meaning |
|---|---|---|
| 🟢 Green | `[OK]` | Operation succeeded |
| 🟡 Yellow | `[WARN]` | Non-fatal issue (e.g. missing file) |
| 🔴 Red | `[ERR]` | Operation failed — details follow |
| 🔵 Blue/Purple | `[···]` | In-progress notification |
| Grey | `[SKIP]` | File already exists or in skip range |

The **CLR** button in the top-right of the log panel clears the output. Each new run auto-clears the previous log.

---

## Data Flow Diagram

```
INPUT FILESYSTEM                PIPELINE                OUTPUT FILESYSTEM
─────────────────               ─────────────           ─────────────────

SOURCE\                         ┌──────────┐
  CHAPTER 001\                  │ STAGE 1  │
  ├── 001.png  ──────────────── │ img2pdf  │ ──────▶  INTERMEDIATE\
  ├── 002.png                   │ convert  │            CHAPTER 001.PDF
  └── 003.png                   └──────────┘            CHAPTER 002.PDF
  CHAPTER 002\                                           ...
  ├── 001.png  ──────────────── (same logic)
  └── ...
                                ┌──────────┐
INTERMEDIATE\                   │ STAGE 2  │
  CHAPTER 001.PDF ───────────── │ shutil   │ ──────▶  INTERMEDIATE\
  CHAPTER 002.PDF               │ .move()  │            CHAPTER 001-005\
  CHAPTER 003.PDF               └──────────┘            CHAPTER 006-010\
  ...                                                    ...

INTERMEDIATE\                   ┌──────────┐
  CHAPTER 001-005\ ──────────── │ STAGE 3  │
  ├── CHAPTER 001.PDF           │  pypdf   │ ──────▶  OUTPUT\
  ├── CHAPTER 002.PDF           │  merge   │            CHAPTER 001-005.PDF
  └── ...                       └──────────┘            CHAPTER 006-010.PDF
                                                         ...
```

---

## Folder & File Naming Conventions

The pipeline uses a specific naming convention to identify chapter numbers. Understanding this prevents `[WARN] Unrecognised folder` messages.

### Chapter Folder Names (Stage 1 Input)

The folder name **must contain the word `CHAPTER` followed by a number**. Case-insensitive. Recommended **Bulk Rename Utility** for rename the `CHAPTER` and numbering `001, 002, 003....090, 010, 011, 012.... 099, 100, 101 And Go On` like this.

| Folder Name | Parsed Chapter # | Valid? |
|---|---|---|
| `CHAPTER 031` | 31 | ✅ |
| `Chapter 5` | 5 | ✅ |
| `chapter 100` | 100 | ✅ |
| `CHAPTER  42` (extra space) | 42 | ✅ |
| `Vol 1 Chapter 31` | ❌ (can't parse) | ⚠️ Warn |
| `031` | ❌ (no "CHAPTER") | ⚠️ Warn |

### Output PDF Names (Stage 1 Output)

Output PDFs are always named as the **uppercase folder name + `.PDF`**:
```
CHAPTER 001  →  CHAPTER 001.PDF
chapter 5    →  CHAPTER 5.PDF
```

### Batch Folder Names (Stage 2 Output)

Always formatted as:
```
CHAPTER {start:03d} - CHAPTER {end:03d}
```
Example: `CHAPTER 031 - CHAPTER 038`

> The 3-digit zero-padding ensures alphabetical and numerical sort order match.

---

## Building a Standalone .EXE

Convert `manga_pipeline.py` into a single `.exe` file that runs on any Windows PC **without requiring Python to be installed**.

---

### Method 1 — PyInstaller (Recommended)

PyInstaller is the most mature, widely tested Python packaging tool. Best choice for this project.

#### Install PyInstaller

```bash
pip install pyinstaller
```

#### Basic Build (Single File)

```bash
pyinstaller --onefile --windowed manga_pipeline.py
```

| Flag | Effect |
|---|---|
| `--onefile` | Packs everything into one `.exe` |
| `--windowed` | No console window (GUI-only, no black terminal) |

Find your executable at: `dist\manga_pipeline.exe`

---

#### Full Production Build (Recommended)

```bash
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "MangaPDFPipeline" ^
  --icon icon.ico ^
  --add-data "README.md;." ^
  manga_pipeline.py
```

| Flag | Effect |
|---|---|
| `--name "MangaPDFPipeline"` | Sets the output exe filename |
| `--icon icon.ico` | Custom window icon (remove if no icon file) |
| `--add-data "README.md;."` | Bundles the README inside the exe |

> **Windows path separator:** Use `;` (semicolon) on Windows for `--add-data`. On macOS/Linux use `:` (colon).

---

#### Handling CustomTkinter Assets

CustomTkinter ships with theme assets (JSON files, images) that PyInstaller sometimes misses. Fix this with a hook:

```bash
pip install pyinstaller-hooks-contrib
```

Then build with:

```bash
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "MangaPDFPipeline" ^
  --collect-data customtkinter ^
  manga_pipeline.py
```

The `--collect-data customtkinter` flag ensures all theme files are bundled.

---

#### Post-Build File Structure

```
manga-pdf-pipeline\
├── dist\
│   └── MangaPDFPipeline.exe    ← Your final executable
├── build\                      ← Temporary build artifacts (delete this)
├── MangaPDFPipeline.spec       ← PyInstaller spec file (keep for rebuilds)
└── manga_pipeline.py
```

You only need to distribute `MangaPDFPipeline.exe`. The `build\` folder and `.spec` file are for your own rebuild use only.

---

#### Using the .spec File for Reproducible Builds

After your first build, PyInstaller generates a `MangaPDFPipeline.spec` file. Future rebuilds are faster using it:

```bash
pyinstaller MangaPDFPipeline.spec
```

To edit the spec file for advanced control (e.g. adding hidden imports):

```python
# MangaPDFPipeline.spec  — edit the hiddenimports list:
a = Analysis(
    ['manga_pipeline.py'],
    hiddenimports=['PIL', 'img2pdf', 'pypdf'],
    ...
)
```

---

### Method 2 — Nuitka (Faster Runtime)

Nuitka compiles Python to native C++ code. The resulting `.exe` starts faster and runs with lower memory overhead. More complex setup — recommended only if you need performance.

#### Install

```bash
pip install nuitka
# Also requires a C compiler — install MinGW or MSVC (Visual Studio Build Tools)
```

#### Build

```bash
python -m nuitka ^
  --onefile ^
  --windows-disable-console ^
  --follow-imports ^
  --include-package=customtkinter ^
  --include-package=img2pdf ^
  --include-package=pypdf ^
  --output-filename=MangaPDFPipeline.exe ^
  manga_pipeline.py
```

#### Nuitka vs PyInstaller

| | PyInstaller | Nuitka |
|---|---|---|
| Build time | Fast (30–60 sec) | Slow (3–10 min) |
| Startup speed | Moderate | Fast |
| EXE size | 20–40 MB | 15–30 MB |
| Setup complexity | Low | Medium-High |
| Compatibility | Excellent | Very Good |

---

### Method 3 — cx_Freeze

A solid alternative, especially for multi-file projects. Less commonly used but reliable.

#### Install

```bash
pip install cx_Freeze
```

#### Create `setup_cx.py`

```python
from cx_Freeze import setup, Executable
import sys

build_exe_options = {
    "packages": ["customtkinter", "img2pdf", "pypdf", "tkinter"],
    "excludes": [],
    "include_files": [],
}

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="MangaPDFPipeline",
    version="1.0",
    description="Manga PDF Pipeline — Convert, Organize, Merge",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "manga_pipeline.py",
            base=base,
            target_name="MangaPDFPipeline.exe",
        )
    ],
)
```

#### Build

```bash
python setup_cx.py build
```

Output is in `build\exe.win-amd64-3.x\MangaPDFPipeline.exe`

---

### EXE Comparison Table

| | PyInstaller | Nuitka | cx_Freeze |
|---|---|---|---|
| **Difficulty** | ⭐ Easy | ⭐⭐⭐ Hard | ⭐⭐ Medium |
| **Build Time** | Fast | Very Slow | Medium |
| **Output** | Single `.exe` | Single `.exe` | Folder |
| **EXE Size** | ~25–40 MB | ~15–25 MB | ~30–50 MB |
| **Startup** | 1–3 sec | < 1 sec | 1–2 sec |
| **Antivirus FP** | Common | Rare | Rare |
| **CustomTkinter** | ✅ With hook | ✅ | ✅ |
| **Recommended For** | Most users | Performance | Multi-file projects |

> **Antivirus Note:** PyInstaller `.exe` files often trigger false-positive antivirus warnings because the PyInstaller bootloader is a common tool also used in malware distribution. This is a known issue. The file is safe — you built it yourself. To reduce false positives: use a custom `--icon`, sign the binary with a code-signing certificate (advanced), or use Nuitka which has far fewer false positives.

---

### Troubleshooting the EXE Build

**Problem:** `ModuleNotFoundError` when running the `.exe`

```bash
# Fix: Add the missing module as a hidden import
pyinstaller --onefile --windowed --hidden-import=MODULE_NAME manga_pipeline.py
```

Common hidden imports for this project:
```bash
--hidden-import=PIL
--hidden-import=img2pdf
--hidden-import=pypdf._crypt_filters
```

---

**Problem:** CustomTkinter themes not loading (grey/broken UI)

```bash
# Fix: Collect all customtkinter data files
pyinstaller --onefile --windowed --collect-data customtkinter manga_pipeline.py
```

---

**Problem:** EXE opens then immediately closes

```bash
# Debug: Remove --windowed to see the console output
pyinstaller --onefile manga_pipeline.py
# Run the EXE from cmd.exe to see the error message
```

---

**Problem:** Very large EXE size (> 100 MB)

```bash
# Fix: Exclude unused packages
pyinstaller --onefile --windowed ^
  --exclude-module matplotlib ^
  --exclude-module numpy ^
  --exclude-module scipy ^
  manga_pipeline.py
```

---

**Problem:** EXE doesn't show a window at all (silent failure)

This is usually a missing `tkinter` or display issue. Test with:
```bash
python -c "import tkinter; tkinter.Tk().mainloop()"
```
If this fails, re-install Python with **tcl/tk support** checked during setup.

---

## Configuration Reference

All parameters are configured through the GUI. Here is a full reference:

| Parameter | Type | Default | Description |
|---|---|---|---|
| **IMAGE SOURCE** | Directory Path | — | Root folder containing chapter subfolders with image files |
| **INTERMEDIATE** | Directory Path | — | Working directory for flat PDFs and batch subfolders |
| **FINAL OUTPUT** | Directory Path | — | Destination for finished merged PDFs |
| **Batch Size** | Integer | `5` | Number of chapters per batch folder / merged PDF |
| **Start Chapter** | Integer | `1` | First chapter number in the processing range |
| **End Chapter** | Integer | `999` | Last chapter number in the processing range |
| **Skip From** | Integer | `110` | First chapter to exclude from Stage 1 conversion |
| **Skip To** | Integer | `130` | Last chapter to exclude from Stage 1 conversion |
| **Image Extensions** | Checkboxes | `.png .jpg .jpeg .webp` | File types to include as pages |
| **Custom Extensions** | Text | *(blank)* | Additional extensions (comma-separated, e.g. `.bmp, .tiff`) |

---

## Edge Cases & Known Behaviours

### Idempotency

Every stage is **safe to re-run**. The pipeline checks for existing outputs before processing:

- **Stage 1:** If `CHAPTER 001.PDF` already exists in the output folder, that chapter is skipped with `[SKIP] Already exists`.
- **Stage 2:** Batch folders are created with `exist_ok=True` — no error if they already exist. Files that have already been moved will show `[WARN] Missing` (because they're no longer in the source), but this is harmless.
- **Stage 3:** If `CHAPTER 001 - CHAPTER 005.PDF` already exists in the output, the entire folder merge is skipped.

### Chapter Number Parsing

The parser extracts the integer after stripping the word `CHAPTER` (case-insensitive). A folder named `CHAPTER  042` (double space) parses as `42`. A folder that cannot yield an integer logs `[WARN] Unrecognised folder` and is skipped — it does not stop the run.

### Image Sort Order

Within each chapter folder, images are sorted **by filename, case-insensitively**. This means:

```
001.png, 002.png, 003.png ...  → correct order ✅
1.png, 10.png, 2.png           → alphabetical, NOT numerical ⚠️
```

If your images use single-digit names without zero-padding, rename them to `001.png`, `002.png`, etc. beforehand.

### Duplicate Extension Detection

The image collector deduplicates using a `set()`. If a folder contains both `001.PNG` (uppercase) and `001.png` (lowercase), only one is included.

### Stage 2 and Source = Destination

If you set the INTERMEDIATE and FINAL OUTPUT to the same directory, Stage 2 and 3 can coexist. Stage 3 will skip any folder-named PDF that already exists and will only process actual subdirectories.

---

## FAQ

**Q: Can I use this for any manga?**
Yes. It works for any chapter-based image collection as long as folders follow the `CHAPTER N` **EXAMPLE: CHAPTER 001 0R CHAPTER 035 OR CHAPTER 270** naming convention.

---

**Q: What happens if a chapter has no images?**
Stage 1 logs `[SKIP] No images found: CHAPTER XXX` and counts it as a non-fatal error. The run continues with the next chapter.

---

**Q: Can SOURCE and INTERMEDIATE be the same folder?**
Yes, but be careful: Stage 1 writes PDFs into that folder, and Stage 2 then moves them into subfolders inside the same folder. The pipeline handles this cleanly as long as your chapter subfolders only contain images, not PDFs.

---

**Q: Can I run Stage 3 without running Stages 1 and 2 first?**
Yes. If you already have batch subfolders with PDFs, point Stage 3's SOURCE at that directory and it will merge them. Each stage is fully independent.

---

**Q: The progress bar jumps to 100% instantly. Is that a bug?**
No. For small collections (< 10 chapters), each stage completes so fast that the progress bar appears to jump. The log panel will show the correct per-file output.

---

**Q: Does this work on macOS and Linux?**
Yes, with the same `pip install` step. The GUI uses CustomTkinter which is cross-platform. File paths use Python's `pathlib` and `os.path`, so forward/backslash differences are handled automatically.

---

**Q: The `.exe` is flagged by antivirus. Is it safe?**
Yes — if you built it yourself from this source code. PyInstaller-packaged executables are frequently flagged as false positives. See the [Antivirus Note](#exe-comparison-table) section above.

---

**Q: How do I add support for `.cbz` or `.cbr` files?**
These are zip/rar archives, not image formats. You'd need to extract them first (with `zipfile` for `.cbz`), then point Stage 1 at the extracted image folders. Native `.cbz`/`.cbr` support is not in scope for this version.

---

<div align="center">

```
╔═══════════════════════════════════════╗
║   Built with precision. Runs silent.  ║
║                SA SUJON               ║
╚═══════════════════════════════════════╝
```

*Python · CustomTkinter · img2pdf · pypdf*

</div>
