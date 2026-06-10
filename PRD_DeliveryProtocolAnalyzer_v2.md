# Product Requirements Document
# Delivery Protocol Analyzer — Python CLI Script

| Field | Value |
|---|---|
| **Document version** | 2.0 |
| **Status** | Ready for development |
| **Date** | 2026-06-03 |
| **Product name** | Delivery Protocol Analyzer |
| **Delivery form** | Python script, run locally in terminal |
| **Platform** | macOS · Windows |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Goals and Non-Goals](#2-goals-and-non-goals)
3. [User and Deployment Context](#3-user-and-deployment-context)
4. [CLI Interaction Flow](#4-cli-interaction-flow)
5. [Directory Structure Contract](#5-directory-structure-contract)
6. [PDF Specification](#6-pdf-specification)
7. [Processing Pipeline](#7-processing-pipeline)
8. [Calculations](#8-calculations)
9. [Output Specification — CSV](#9-output-specification--csv)
10. [Terminal Output Specification](#10-terminal-output-specification)
11. [Error Catalog](#11-error-catalog)
12. [Non-Functional Requirements](#12-non-functional-requirements)
13. [Tech Stack](#13-tech-stack)
14. [Deployment](#14-deployment)

---

## 1. Executive Summary

The Delivery Protocol Analyzer is a Python CLI script that processes sampling protocol PDFs from a structured local folder, extracts delivery weight and precious metal assay data, and exports the results as a semicolon-delimited CSV file.

The user launches the script in a terminal. The script prompts for the protocols folder path, a date range, and confirms the output location. It then traverses the folder tree, identifies all sampling protocols whose date of receipt falls within the specified window, extracts and calculates the relevant values, and writes a CSV file to a predefined output folder.

No data is stored at any point. No network access occurs. The script has no UI beyond the terminal.

---

## 2. Goals and Non-Goals

### Goals

- Parse machine-readable sampling protocol PDFs from two smelter templates (KV and BRX) in a layout-tolerant way.
- Filter deliveries by date of receipt against a user-defined date range.
- Extract weight data and precious metal assay concentrations and convert them to kilograms with 5 decimal place precision.
- Produce a semicolon-delimited CSV matching the defined output structure.
- Log all processing activity, skipped files, exclusions, and errors clearly in the terminal.
- Run on macOS and Windows with no dependencies beyond Python and two pip packages.

### Non-Goals

- No GUI, no web interface, no installer.
- No database, no persistent storage, no logging to disk.
- No network access of any kind.
- No OCR — all PDFs are machine-readable (digitally authored).
- No support for templates other than KV and BRX in this version.
- No repair or correction of malformed PDFs.

---

## 3. User and Deployment Context

| Attribute | Value |
|---|---|
| User | Single, non-technical (operations role) |
| OS | macOS or Windows |
| Python | Installed once by developer on client machine |
| Dependencies | Installed once by developer via pip |
| Network | Not required |
| Data sensitivity | High — billing and precious metal assay data |
| Run frequency | Approximately monthly |
| Authentication | None |

The developer installs Python and the two required packages on the client machine once. The client runs the script by opening a terminal, navigating to the script folder, and typing `python analyze.py`.

---

## 4. CLI Interaction Flow

The script uses a combination of path confirmations and sequential `input()` prompts. All validation happens immediately after each entry. On invalid input, the same prompt is re-asked with an inline error message. The user can press `Ctrl+C` at any point to abort.

```text
─────────────────────────────────────────────
  Delivery Protocol Analyzer
─────────────────────────────────────────────

  Configure this run:

  [1/3]  Output folder [/Users/MIESZKO/Desktop/output-protocols-analyzed]: ↵
         ✓ confirmed

  [2/3]  Date from (DD.MM.YYYY): 01.01.2026
  [3/3]  Date to   (DD.MM.YYYY): 07.06.2026

─────────────────────────────────────────────
  Ready to run
  Window:    01.01.2026 → 07.06.2026
  Output:    /Users/MIESZKO/Desktop/output-protocols-analyzed
─────────────────────────────────────────────
  Press Enter to start or Ctrl+C to abort: ↵

  Processing...
```

### Prompt specifications

| Step | Prompt / Confirmation | Default | Validation | Re-prompt on failure |
|---|---|---|---|---|
| 1 | Output folder path | Constant `OUTPUT_FOLDER` at top of script | Path exists or can be created | Yes — show reason |
| 2 | Date from | None | Parseable as DD.MM.YYYY, not in future | Yes — show format/future error |
| 3 | Date to | None | Parseable as DD.MM.YYYY, ≥ Date from | Yes — show reason |

After step 3, the script displays a confirmation summary (date window, output path) and waits for a final Enter before execution begins.

### Output folder default

A constant `OUTPUT_FOLDER` is defined at the top of `analyze.py`. The developer sets this once during installation. The user sees the current value at prompt [1/4] and can accept it with Enter, or override it by typing a new path. If it does not exist, the script creates it automatically.

---

## 5. Directory Structure Contract

### 5.1 Expected Folder Tree

To ensure original data remains secure and untouched, the system implements a strict read-only folder contract:
* **Master Folder** (`MASTER_FOLDER`): The original database of all supplier folders. **The script reads files directly from here but never alters, moves, or deletes anything.**
* **Archive Folder** (`ARCHIVE_FOLDER`): Holds copies of successfully processed files and failed files temporarily after a successful run.

The master folder expects the following tree:
```
{MASTER_FOLDER}/
└── {SupplierName}/              ← e.g. Cronimet Nordic (supplier directory name)
    └── {Year}/                  ← e.g. 2026 (four-digit year)
        └── {Month}/             ← e.g. 03 (two-digit month, 01-12)
            └── {DeliveryNumber}/← e.g. 26002238 (numeric delivery ID)
                ├── Sampling protocol 26002238.pdf
                └── [other files — ignored silently]
```

> **Wrapper Folder Independence:** If the user wraps the supplier folders in an arbitrary folder inside `{MASTER_FOLDER}` (e.g. `{MASTER_FOLDER}/{WrapperFolder}/Supplier/...`), the script automatically and dynamically traverses the tree to locate the supplier directories by searching for folders containing 4-digit year directories. This makes execution completely agnostic to wrapper folder names.

### 5.2 Naming Conventions

| Level | Format | Notes |
|---|---|---|
| Supplier folder | Alphanumeric string | Used only as folder structure. Not used for Smelter Code logic. |
| Year folder | 4-digit integer | e.g. `2026`. Used to determine the prefix matching for Smelter Code logic. |
| Month folder | 2-digit integer | e.g. `01` to `12`. Traversed sequentially to find deliveries. |
| Delivery folder | Numeric string | e.g. `56589` or `26002238`. If the folder starts with the last 2 digits of the year (e.g. `26`), Smelter Code is `BRX`. Otherwise, it is `KK`. |
| Protocol PDF | Starts with `Sampling protocol` or `Sampling_protocol` (case-insensitive), ends with `.pdf` | Files not matching this pattern are ignored silently. |

### 5.3 Files to Ignore

Inside any delivery folder, silently skip:
- Any file whose name does not begin with `sampling protocol` or `sampling_protocol` (case-insensitive).
- Any non-`.pdf` file.
- Hidden files (names beginning with `.`).
- System files (`Thumbs.db`, `.DS_Store`, `desktop.ini`).

No error is raised for ignored files. They are not mentioned in terminal output.

### 5.4 Multi-Position vs. Single-Position Deliveries

A delivery folder containing **more than one** matching protocol PDF is a **multi-position delivery**.
A delivery folder containing **exactly one** matching protocol PDF is a **single-position delivery**.

This classification is based on the total count of matching PDFs in the folder, regardless of how many fall within the date window. This distinction affects the output delivery number format — see Section 9.2.

---

## 6. PDF Specification

### 6.1 Two Templates

| Template ID | Issuer | Language |
|---|---|---|
| **KV** | KOVOHUTY, a.s. | English / Slovakian |
| **BRX** | MONTANWERKE BRIXLEGG AKTIENGESELLSCHAFT | German + English bilingual |

**Parser strategy:** Support multilingual vocabulary mapping across English, German, and Slovakian to handle regional variations, bilingual labels, and layout extraction anomalies (where values appear on German/Slovakian label lines instead of English lines).

### 6.2 Fields Extracted

The script extracts exactly the following fields from each protocol PDF.

| Field | Multilingual Label Anchor Options | Used for | Notes |
|---|---|---|---|
| Date of receipt | `Date of receipt` / `Eingangsdatum` / Slovak equivalent or first date fallback | Date-window filtering + CSV output | Format: `DD.MM.YYYY` |
| Position number | `Pos.` | Delivery number construction + duplicate detection | Integer, e.g. `01`, `02` |
| Wet weight | `Wet weight`, `Nassgewicht`, `mokrá/vlhká hmotnosť`, `Feuchtgewicht` | CSV output | European number format |
| Moisture | `Moisture`, `Nässe`, `Feuchtigkeit`, `Feuchte`, `vlhkosť` | CSV output | European number format |
| Dry weight | `Dry weight`, `Trockengewicht`, `suchá hmotnosť`, `sušina`, `hmotnosť za sucha` | CSV output + calculation base | European number format |
| Silver | `Ag` followed by value and `g/t` | Calculation | Optional — 0 if absent |
| Gold | `Au` followed by value and `g/t` | Calculation | Optional — 0 if absent |
| Palladium | `Pd` followed by value and `g/t` | Calculation | Optional — 0 if absent |
| Platinum | `Pt` followed by value and `g/t` | Calculation | Optional — 0 if absent |

**Fields explicitly ignored:**
- `Date of receipt:` — not extracted, not used anywhere.
- `Submission number:` / `Submisson number:` — not extracted, not used anywhere.
- Cu percentage — not extracted.
- Mixture / lot breakdown percentages — not extracted.
- Supplier name, contract number, material name, sample number, plate/container number — not extracted.

### 6.3 Date of Receipt — Label Disambiguation

Every PDF contains two date-like fields:
- `Date of receipt:` / `Eingangsdatum` (or Slovak equivalent) — arrival date at smelter. **This is the one used.**
- `Date:` / `Datum:` — finalization/signing date at bottom of document. **Ignored entirely.**

The parser first checks for specific labels (`Date of receipt`, `Eingangsdatum`, `Dátum prijatia`, `Dátum dodania`, `Dátum doručenia`). If it doesn't find them, it falls back to extracting the **first date** formatted as `DD.MM.YYYY` found in the full extracted text.

### 6.4 Position Field

The `Pos.` field contains an integer (sometimes zero-padded: `01`, `02`). Parse as integer. Used to:
1. Construct the delivery number suffix in the output CSV.
2. Detect duplicate positions within a delivery folder.

### 6.5 Number Format

All numeric values use European locale notation: dot = thousands separator, comma = decimal separator.

**Parsing rule:** Strip all `.` characters, replace `,` with `.`, then parse as float.

### 6.6 Extraction Strategy

Use `pdfplumber` to extract full page text as a single string. Apply regex patterns with vocabulary alternatives:

```python
import re

# Date of receipt — primary label match, then fallback
# (pseudo-code regexes represented here)

# Position number
re.search(r"Pos\.?\s*(\d+)", text)

# Wet weight (English, German, Slovakian)
re.search(
    r"(?:Wet[ \t]*weight|Nassgewicht|mokr[aá][ \t]*hmotnos[tť]|vlhk[aá][ \t]*hmotnos[tť]|Feuchtgewicht|hmotnos[tť][ \t]*za[ \t]*mokra)"
    r"(?:[ \t]*\[?kg\]?)?[ \t]*:[ \t]*([\d.,]+)",
    text, re.IGNORECASE
)

# Moisture (English, German, Slovakian)
re.search(
    r"(?:Moisture|N[aä]sse|Feuchtigkeit|Feuchte|vlhkos[tť])"
    r"(?:[ \t]*\[?%\]?)?[ \t]*:[ \t]*([\d.,]+)",
    text, re.IGNORECASE
)

# Dry weight (English, German, Slovakian)
re.search(
    r"(?:Dry[ \t]*weight|Trockengewicht|such[aá][ \t]*hmotnos[tť]|su[sš]ina|hmotnos[tť][ \t]*za[ \t]*sucha)"
    r"(?:[ \t]*\[?kg\]?)?[ \t]*:[ \t]*([\d.,]+)",
    text, re.IGNORECASE
)

# Precious metals
re.search(r"\bAg\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
re.search(r"\bAu\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
re.search(r"\bPd\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
re.search(r"\bPt\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
```
```
---

## 7. Processing Pipeline

### 7.1 Algorithm

```
FUNCTION run(date_from, date_to):

  1. Validate path settings and folder permissions:
     - Master Folder exists and contains files.
     - Output & Archive Folders are writable.
     Halt with clean error on pre-flight failure (see Section 11).

  2. suppliers = sorted subdirectories of Master Folder (alphabetical)

  3. years_needed = calendar years spanned by [date_from, date_to]

  4. result_rows = []
     successfully_processed_files = []
     failed_files = []
     protocols_processed = 0
     protocols_excluded = 0
     protocols_failed = 0

  5. FOR each supplier in suppliers:
       FOR each year in years_needed:
         year_path = Master/{supplier}/{year}/
         IF year_path does not exist → skip silently

         FOR each month in 01..12:
           month_path = Master/{supplier}/{year}/{month}/
           IF month_path does not exist → skip silently

           delivery_folders = sorted subdirectories of month_path (ascending)

           FOR each delivery_folder in delivery_folders:
             protocol_files = files in delivery_folder matching naming pattern
                              (Section 5.3), sorted ascending by filename

             IF len(protocol_files) == 0 → skip silently

             DUPLICATE POSITION CHECK (before processing files):
               positions_seen = {}
               FOR each file in protocol_files:
                 - Extract Pos. field from PDF.
                 - IF pos in positions_seen → HALT → ERROR_DUPLICATE_PROTOCOL
                 positions_seen[pos] = file

             FOR each pdf_file in protocol_files:
               protocols_processed += 1
               
               - Attempt text extraction & parsing of weights/dates
                IF parse fails (e.g. unreadable file or missing weight fields):
                  - Log red [FAIL] message in terminal with specific error reason.
                  - protocols_failed += 1
                  - failed_files.append(pdf_file)
                  - CONTINUE (exclude the file from CSV but continue execution)

               IF date NOT in [date_from, date_to]:
                 - Log [--] status in terminal.
                 - protocols_excluded += 1
                 - CONTINUE (exclude from CSV but continue execution)

               - Calculate precious metal quantities in kg (rounded to 5 decimals).
               - Determine smelter_code based on delivery_folder prefix.
               - Format delivery_number (append "-{pos}" if multi-position).

                result_rows.append({
                  smelter_code, delivery_number, delivery_date,
                  quantity_kg, h2o_pct, dry_quant_kg,
                  ag_kg, au_kg, pd_kg, pt_kg
                })
                - Log [OK] status in terminal.
                - successfully_processed_files.append(pdf_file)

  6. SORT result_rows:
       primary:   smelter_code ascending
       secondary: delivery_number ascending (natural sort on numeric base)
       tertiary:  position number ascending

  7. ASSIGN Lp: sequential integer starting at 1

  8. COMPUTE totals row (Section 8.2)

  9. WRITE CSV (Section 9)

  10. PRINT run summary (processed, included, excluded, failed) to terminal.

  11. ARCHIVE & CLEANUP:
      - Create unique folders in Archive: `samples_run_X` and `failed_samples_run_X`
      - Copy successfully processed files into `samples_run_X` maintaining original tree structure.
      - Copy failed files into `failed_samples_run_X` maintaining original tree structure.
      - Prompt user to verify CSV:
        - Press Enter → delete both temporary archive folders.
        - Press Ctrl+C → keep the temporary archive folders for review.
```

### 7.2 Date Range and Year Traversal

- Both `date_from` and `date_to` are inclusive.
- If the date range spans calendar years, the script traverses all spanned year folders.
- The date used for filtering is the date of receipt (`Date of receipt`/`Eingangsdatum`) parsed from the PDF.

### 7.3 Duplicate Detection

A duplicate is defined as: two or more PDF files within the same delivery folder whose `Pos.` field value resolves to the same integer. Duplicate detection runs before any file in that delivery folder is processed. On detection: halt immediately, report both conflicting file paths and the delivery folder path, and do not write any output.

---

## 8. Calculations

### 8.1 Precious Metal Quantities

Assay concentrations in the PDF are in **grams per metric tonne (g/t)**.

```
metal_kg = concentration_g_per_t × dry_weight_kg ÷ 1,000,000
```

Derivation: 1 g/t = 1 g per 1,000 kg. Therefore:
`metal_total_g = concentration × (dry_weight_kg ÷ 1,000)`, then `÷ 1,000` to convert g → kg.

All four metals use this formula. When a metal is absent from the PDF, its concentration = 0, therefore `metal_kg = 0.00000`.

**Precision:** All calculated metal values are rounded to **5 decimal places** in the output. Internal floating point arithmetic must use Python's `round(value, 5)` before writing to CSV.

### 8.2 Totals Row

Appended as the last row after all data rows.

| Column | Totals row value |
|---|---|
| Lp | `Total:` |
| Delivery number | empty |
| Delivery date | empty |
| Smelter code | empty |
| Quantity kg | `SUM` of all rows |
| H2O[%] | empty |
| Dry quant. kg | `SUM` of all rows |
| Ag kg | `SUM` of all rows |
| Au kg | `SUM` of all rows |
| Pd kg | `SUM` of all rows |
| Pt kg | `SUM` of all rows |

Totals are also rounded to 5 decimal places.

### 8.3 Dry Weight

The dry weight value is read directly from the PDF (`Dry weight [kg]:` field) and written to the output as-is. It is not recalculated by the script. The smelter's computed value is trusted.

---

## 9. Output Specification — CSV

### 9.1 Format

| Property | Value |
|---|---|
| File format | CSV |
| Delimiter | Semicolon `;` |
| Decimal separator | Period `.` |
| Encoding | UTF-8 |
| Line endings | System default (Python `csv` module default) |
| Header row | Yes — first row |

> **Rationale for semicolon delimiter:** European Excel installations use semicolons as the CSV delimiter because commas are reserved as decimal separators in regional settings. A comma-delimited file would open as a single unformatted column in European Excel without manual import configuration.

### 9.2 Columns

| # | Header | Source | Type | Precision |
|---|---|---|---|---|
| 1 | `Lp` | Generated | Integer | — |
| 2 | `Delivery number` | Folder name + Pos. field | String | — |
| 3 | `Delivery date` | PDF `Date of receipt` | String | `DD.MM.YYYY` |
| 4 | `Smelter code` | Supplier folder name | String | — |
| 5 | `Quantity kg` | PDF `Wet weight [kg]:` | Float | 3 decimal places |
| 6 | `H2O[%]` | PDF `Moisture [%]:` | Float | 2 decimal places |
| 7 | `Dry quant. kg` | PDF `Dry weight [kg]:` | Float | 3 decimal places |
| 8 | `Ag kg` | Calculated | Float | 5 decimal places |
| 9 | `Au kg` | Calculated | Float | 5 decimal places |
| 10 | `Pd kg` | Calculated | Float | 5 decimal places |
| 11 | `Pt kg` | Calculated | Float | 5 decimal places |

### 9.3 Delivery Number Format

| Delivery type | Format | Example |
|---|---|---|
| Single-position (1 protocol file in folder) | `{folder_name}` | `56729` |
| Multi-position (2+ protocol files in folder) | `{folder_name}-{pos_integer}` | `56589-1`, `56589-2` |

Position integer = the integer value of the `Pos.` field from inside the PDF, stripped of leading zeros (`01` → `1`).

### 9.4 Row Ordering

1. Smelter code — alphabetical ascending
2. Delivery number base (numeric, ascending)
3. Position number (ascending)

### 9.5 Output Filename

```
DeliveryReport_{DDMMYYYY}_{DDMMYYYY}.csv
```

Example: `DeliveryReport_01052026_31052026.csv`

Written to the confirmed output folder. If a file with the same name already exists in the output folder, the script appends a counter suffix: `DeliveryReport_01052026_31052026_2.csv`, `_3.csv`, etc. It never silently overwrites an existing file.

---

## 10. Terminal Output Specification

### 10.1 During Processing

For each protocol file processed, print one status line:

```text
  [OK]  Cronimet Nordic / 2026 / 26002238  →  finalized 24.03.2026
  [OK]  Cronimet Nordic / 2026 / 26002239  →  finalized 24.03.2026
  [--]  Cronimet Nordic / 2026 / 57100-1  →  finalized 12.04.2026  (outside window)
  [FAIL] Cronimet Nordic / 2026 / Sampling protocol 26002658.pdf  →  Missing Wet weight [kg] field
```

- `[OK]` — protocol extracted and included in results.
- `[--]` — protocol detected, date of receipt outside window, excluded from results.
- `[FAIL]` — extraction error (corrupt file, missing weight/date fields). The file is excluded, but the run continues.

### 10.2 Run Summary (on success)

Printed after the CSV is written:

```text
─────────────────────────────────────────────
  Run complete
─────────────────────────────────────────────
  Protocols processed:   104
  Deliveries included:   33
  Protocols excluded:    50
  Protocols failed:      0

  Output written to:
  /Users/MIESZKO/Desktop/output-protocols-analyzed/DeliveryReport_01012026_07062026.csv
─────────────────────────────────────────────
```

- **Protocols processed**: Total PDFs that matched the naming pattern and were opened.
- **Deliveries included**: Count of unique delivery numbers that contributed at least one row.
- **Protocols excluded**: PDFs whose date of receipt fell outside the window.
- **Protocols failed**: PDFs with parsing errors that were skipped.

### 10.3 Error Output (on halt)

```text
─────────────────────────────────────────────
  [ERR]  Run halted — duplicate protocol detected

  Delivery folder:
    /Users/MIESZKO/Desktop/.../samples/Dostawcy-kopia/Amra/2026/03/57001/

  Conflicting files:
    Sampling protocol 57001A.pdf  (Pos. 01)
    Sampling protocol 57001B.pdf  (Pos. 01)

  Both files claim position 01. Remove or rename the
  duplicate before rerunning.
─────────────────────────────────────────────
  No output file was written.
─────────────────────────────────────────────
```


| Code | Trigger | Message shown |
|---|---|---|
| `E06` | Date of receipt cannot be parsed from PDF text | `Cannot extract date of receipt from: {path}. File was read but no valid date found. Verify the file manually.` |
| `E07` | Pos. field cannot be parsed | `Cannot extract position number (Pos.) from: {path}.` |
| `E08` | Wet weight, moisture, or dry weight cannot be parsed | `Cannot extract weight data from: {path}. Missing fields: {field_list}.` |
| `E09` | File opens and text is extracted but none of the expected fields are found | `File opened but no recognisable data found: {path}. Template may be unsupported.` |

---

## 12. Non-Functional Requirements

### Privacy

- The script reads files from disk and holds extracted values in memory only.
- Nothing is written to disk except the final CSV at the user-confirmed output path.
- No logging to disk, no temp files, no cache.
- After the script exits, no trace of the processed data remains.

### Precision

- All precious metal calculations are performed as Python `float` arithmetic.
- All metal values written to CSV are rounded to exactly 5 decimal places using `round(value, 5)`.
- Weight values (Quantity kg, Dry quant. kg) are rounded to 3 decimal places.
- Moisture is rounded to 2 decimal places.

### Robustness

- All errors produce specific, actionable messages. No unhandled exceptions reach the terminal as stack traces.
- A top-level `try/except` wraps the main execution and formats any unexpected exception as a clean `[ERR] Unexpected error: {message}` output.
- The script must handle date ranges spanning two calendar years without special user action.

### Performance

- For a typical monthly run (30–150 PDFs), completion time should be under 30 seconds on a standard business laptop.

### Platform

- Tested and working on macOS 12+ and Windows 10 64-bit.
- All file path handling uses `pathlib.Path` throughout — no hardcoded `/` or `\` separators.

---

## 13. Tech Stack

| Component | Library | Notes |
|---|---|---|
| PDF extraction | `pdfplumber` | pip install. Handles both KV and BRX templates. |
| Terminal output | `rich` | pip install. Colored `[OK]` / `[--]` / `[ERR]` lines and summary panels. |
| CSV writing | `csv` | Python stdlib. Semicolon delimiter, UTF-8 encoding. |
| File system | `pathlib` | Python stdlib. Cross-platform path handling. |
| Date parsing | `datetime` | Python stdlib. `strptime(value, "%d.%m.%Y")`. |
| Regex | `re` | Python stdlib. Field extraction from PDF text. |

**No other dependencies.** Two pip packages total: `pdfplumber` and `rich`.

### Installation (run once by developer)

```bash
pip install pdfplumber rich
```

### Running the script

```bash
python analyze.py
```

---

## 14. Deployment

### Developer Setup (one-time, per machine)

1. Install Python 3.11+ on the client machine.
2. Copy `analyze.py` to a permanent folder (e.g. `Documents/Tools/`).
3. Open `analyze.py` and set the `OUTPUT_FOLDER` constant at the top of the file to the client's desired default output path.
4. Run `pip install pdfplumber rich` in the terminal.
5. Verify by running `python analyze.py` and walking through the prompts once.

### Script Configuration Constant

```python
# Set this once during installation. The user sees this value at
# prompt [1/4] and can override it per-run.
OUTPUT_FOLDER = "/Users/jan/Documents/DeliveryReports"
```

On Windows, use a raw string: `r"C:\Users\Jan\Documents\DeliveryReports"`.

### Updates

When a smelter changes their PDF template and a parser regex stops working, the developer updates the relevant regex pattern in `analyze.py` and re-copies the file to the client machine. No installer, no version management required.

### Source Control

`analyze.py` is maintained in a private GitHub repository. The client never interacts with GitHub. The developer pulls updates and redeploys the file manually when needed.
