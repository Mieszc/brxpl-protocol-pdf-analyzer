# brxpl-protocol-pdf-analyzer
Simple desktop script that analyzes pdfs and automates generation of statistics based on them.

## Environment & Setup

To protect your system's Homebrew Python installation, this project relies on an isolated virtual environment (`venv`).

### 1. Activating the Environment
Before running the script or doing any debugging, you must activate the virtual environment:
```bash
source venv/bin/activate
```
*(Your terminal prompt should change to show `(venv)`).*

### 2. Installing Requirements
If dependencies change, install them while the `venv` is activated:
```bash
pip install -r requirements.txt
```

## Directory Structure

- **`analyze.py`**: The main execution script. Run this via `python analyze.py` (after activating `venv`).
- **`requirements.txt`**: List of Python dependencies (currently `pdfplumber` and `rich`).
- **`venv/`**: The isolated virtual environment containing installed packages. (Ignored in Git)

### Safe File Architecture
- **`Master Folder`**: The live database (e.g., your actual protocols folder). The script NEVER modifies this.
- **`Dropzone Folder` (e.g. `samples/`)**: Where you manually drop *copies* of PDFs. Requires a `.safe_dropzone` token.
- **`Archive Folder` (e.g. `archive/`)**: The bin where processed files are moved. We never permanently delete.
- **`Output Folder`**: Where the generated CSV reports are saved.

## Debugging Guide

1. **Path Configuration**: At the top of `analyze.py`, find the section labeled `<INSERT_YOUR_PATH_HERE>`. Update the four path constants with your local testing paths.
2. **Missing Dependencies Error**: If you see an `ImportError` or `Missing dependencies` message when running `analyze.py`, it means you forgot to activate the virtual environment (step 1 above).
3. **Safety Token Missing**: If the script immediately fails with "Safety token missing!", ensure there is a `.safe_dropzone` file in your designated Dropzone Folder.
4. **Master Verification Failure**: If the script fails complaining about "Original missing in Master", it means you accidentally *moved* a file into the dropzone instead of copying it. Move it back to the master folder and make a copy!
