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
- **`Master Folder` (`MASTER_FOLDER`)**: The baseline database of original supplier documents. The script strictly reads data directly from here and **never modifies it**.
- **`Archive Folder` (`ARCHIVE_FOLDER`)**: The temporary directory where copies of processed and failed files are copied on completion for review.
- **`Output Folder` (`OUTPUT_FOLDER`)**: Where the generated CSV reports are saved.

## Debugging Guide

1. **Path Configuration**: At the top of `analyze.py`, find the path constants. Update them with your local testing paths.
2. **Missing Dependencies Error**: If you see an `ImportError` or `Missing dependencies` message when running `analyze.py`, it means you forgot to activate the virtual environment (step 1 above).
3. **IDE / Interpreter Selection**: If your IDE displays import warnings for `pdfplumber` or `rich`, set your IDE's Python interpreter to point to the local `venv/` directory.

