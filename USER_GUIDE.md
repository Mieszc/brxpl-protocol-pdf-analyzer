# User Guide: Delivery Protocol Analyzer

This guide shows you how to use the **Delivery Protocol Analyzer**, a helper tool that automatically reads your supplier protocol PDFs, extracts weights and precious metal percentages, and writes them into a single Excel-ready spreadsheet.

---

## 1. First-Time Setup (Preparing the Environment)

To read PDF files and display colored messages, the tool uses a helper environment (`venv`) and small libraries. 

Before running the tool, follow these steps to prepare your system:

### 1. Open Your Command Terminal
Open your system terminal and navigate to the project folder:
* **macOS / Linux:** Open **Terminal**.
* **Windows (Command Prompt):** Open **Command Prompt** (cmd).
* **Windows (PowerShell):** Open **PowerShell**.

Use the `cd` command to navigate to the project directory:
* **macOS / Linux / Windows Command Prompt / Windows PowerShell:**
  ```cmd
  cd path/to/your/project/brxpl-protocol-pdf-analyzer
  ```

### 2. Turn on the Helper Environment
Run the command matching your operating system and command line program to tell the computer where the tool is:

* **macOS / Linux (Terminal / Bash / Zsh):**
  ```bash
  source venv/bin/activate
  ```
* **Windows (Command Prompt / cmd.exe):**
  ```cmd
  venv\Scripts\activate.bat
  ```
* **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
*(Once you run this, your prompt will show `(venv)` at the beginning, meaning the tool environment is active and ready).*

### 3. Installing or Updating Helper Libraries
If the developer changes the helper libraries, make sure the helper environment is active and run this command:
* **macOS / Linux:**
  ```bash
  pip install -r requirements.txt
  ```
* **Windows (Command Prompt):**
  ```cmd
  pip install -r requirements.txt
  ```
* **Windows (PowerShell):**
  ```powershell
  pip install -r requirements.txt
  ```

---

## 2. Safe Working Folders

To make sure your original files are never altered, deleted, or misplaced, the tool uses a safe 4-folder setup:

* **Master Folder**: The folder containing your actual original database. **The tool never changes anything here.**
* **Dropzone Folder (e.g., `samples/Dostawcy-kopia`)**: This is your sandbox. You copy the PDFs you want to process and paste them here. The tool only reads from these copies.
* **Archive Folder (e.g., `archive/`)**: When the tool successfully finishes, it automatically moves the entire Dropzone folder here as a safeguard, leaving your Dropzone folder completely empty and clean for the next run.
* **Output Folder**: The folder where your final Excel spreadsheets are saved.

> [!WARNING]
> Always **copy and paste** files into the Dropzone. Never cut-and-paste or move original files there directly, or you might accidentally misplace them from the Master folder.

---

## 3. Starting the Tool

Once your helper environment is active, run this command to start:

* **macOS / Linux:**
  ```bash
  python analyze.py
  ```
* **Windows (Command Prompt):**
  ```cmd
  python analyze.py
  ```
  *(Or: `py analyze.py`)*
* **Windows (PowerShell):**
  ```powershell
  python analyze.py
  ```

---

## 4. Setup Questions & Start Confirmation

Once started, the tool verifies your directories and asks four simple questions. For questions with default answers in brackets `[...]`, you can just press **Enter** to accept them, or type a path to change them:

1. **`[1/4] Output folder [default_path]:`**
   * Displays where the spreadsheet will be saved. Press **Enter** to accept or type a new folder path.
2. **`[2/4] Dropzone folder path:`**
   * Confirms the path to the working folder where copies of PDFs are stored.
3. **`[3/4] Date from (DD.MM.YYYY):`**
   * Type the start date of the period you want to check (e.g., `01.05.2026`).
4. **`[4/4] Date to (DD.MM.YYYY):`**
   * Type the end date of the period (e.g., `31.05.2026`).

### Run Summary & Start Confirmation:
After answering the questions, the tool displays a summary:
```text
─────────────────────────────────────────────
  Ready to run
  Window:    01.05.2026 → 31.05.2026
  Output:    /Users/MIESZKO/Desktop/.../output-protocols-analyzed
─────────────────────────────────────────────
  Press Enter to start or Ctrl+C to abort: 
```
* Press **Enter** to start the analysis.
* Press **Ctrl+C** on your keyboard to cancel without making any changes.

---

## 5. Verifying Your Results & Archive Cleanup

After the tool finishes and successfully writes the Excel-compatible spreadsheet, it will present a confirmation prompt in the terminal to help you manage your computer's disk space:

1. **Verify the spreadsheet:** Open the generated CSV in Excel and confirm that the numbers match your expectations.
2. **Review your files:** The entire `Dostawcy-kopia` folder is temporarily moved to the `archive/` directory as a safeguard. You can find all files from this run there if you need to review them or retrieve them.
3. **Decide on cleanup:**
   * **If the results are correct (Delete files):** Press **Enter**. The tool will automatically delete all files inside the `archive/` directory to prevent them from piling up and eating your computer's disk space over time.
   * **If you need to keep or retrieve the files (Keep files):** Press **Ctrl+C**. This stops the cleanup script and leaves the PDFs in the `archive/` directory intact.

---

## 6. Exiting the Tool (Turning Off the Helper Environment)

When the tool finishes running and your spreadsheet is saved, you will see `(venv)` remaining at the beginning of your terminal line. 

To turn off the helper environment and return your terminal to normal, follow these steps:

### 1. Run the Exit Command
Type this command and press **Enter**:
* **macOS / Linux:**
  ```bash
  deactivate
  ```
* **Windows (Command Prompt):**
  ```cmd
  deactivate
  ```
* **Windows (PowerShell):**
  ```powershell
  deactivate
  ```

*(This will remove the `(venv)` prefix, confirming that the helper environment is closed).*

### 2. Close the Window
Once deactivated, you can safely close your Terminal, Command Prompt, or PowerShell window.

---

## 7. What You Will See (Results and Alerts)

The tool lists each file it checks in real time:

* **`[OK]`**: The PDF was read successfully, added to the spreadsheet, and moved to the archive folder.
  ```text
  [OK]  KK_Supplier / 2026 / 56589-1  →  finalized 15.05.2026
  ```
* **`[--]`**: The PDF was read, but its date falls outside your selected range, so it was skipped and left in the dropzone.
  ```text
  [--]  KK_Supplier / 2026 / 57100-1  →  finalized 12.04.2026  (outside window)
  ```
* **`[FAIL]`**: A PDF file has parsing troubles (e.g., is a scanned picture, password-protected, corrupt, or missing weight fields). Instead of stopping the entire process, the tool **excludes** this file, logs the error in red, and proceeds with the other files. It will show up in your final summary count under `Protocols failed`.
* **`[ERR]`**: A critical problem occurred and the tool stopped running immediately. **No spreadsheet is written on error** to prevent partial or incorrect data.

### Critical Errors that Cause a Stop:
* **Duplicate position**: Two or more PDFs inside the same folder represent the same delivery position number.
* **Master folder validation**: If the Master folder doesn't exist, is empty, or is missing a processed PDF.

---

## 8. Understanding the Output Spreadsheet

When the tool finishes successfully, a report is written to your Output folder:

### Filename Format
```text
DeliveryReport_{DDMMYYYY}_{DDMMYYYY}.csv
```
*Example:* `DeliveryReport_01052026_31052026.csv`

> [!NOTE]
> If a report with the same name already exists, the tool automatically adds a counter suffix (e.g., `_2.csv`, `_3.csv`) so you don't lose previous files.

### Spreadsheet Structure:
* **Excel-Compatible (Semicolon delimited)**: Opens automatically in European Excel installations without manual formatting.
* **Decimal Points (Commas)**: Numbers use commas as decimals (e.g., `23080,000` or `3,63`) for direct compatibility with regional Excel settings.
* **Row Sorting**: Rows are automatically sorted:
  1. **Smelter Code** (BRX first, then KK).
  2. **Delivery Number** (lowest to highest).
  3. **Position Number** (lowest to highest).
* **Totals Row**: The last row automatically adds up all weights (`Quantity kg`, `Dry quant. kg`) and precious metal quantities.

---

## 9. Changing Default Folders (Configuration)

The default folders are set in `analyze.py` under the `# PATH CONFIGURATION` section:
* `OUTPUT_FOLDER`: Default report destination.
* `MASTER_FOLDER`: The original database (safety reference).
* `DROPZONE_FOLDER`: Path to the working dropzone directory.
* `ARCHIVE_FOLDER`: Path to the completed archive directory.

### Windows Path Configuration Note
On Windows, folder paths use backslashes (`\`). To prevent Python from interpreting them as escape characters, write them as **raw string literals** by prefixing the path string with `r`:

```python
OUTPUT_FOLDER = r"C:\Users\Jan\Documents\DeliveryReports"
MASTER_FOLDER = r"C:\Users\Jan\Desktop\brxpl\Dostawcy"
DROPZONE_FOLDER = r"C:\Users\Jan\Desktop\mlabsai-work-projects\clients\brxpl-spzoo\smapling-protocol-analyzer\brxpl-protocol-pdf-analyzer\samples\Dostawcy-kopia"
ARCHIVE_FOLDER = r"C:\Users\Jan\Desktop\mlabsai-work-projects\clients\brxpl-spzoo\smapling-protocol-analyzer\brxpl-protocol-pdf-analyzer\archive"
```
