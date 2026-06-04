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

The user launches the script in a terminal. The script prompts for the protocols folder path, a date range, and confirms the output location. It then traverses the folder tree, identifies all sampling protocols whose finalization date falls within the specified window, extracts and calculates the relevant values, and writes a CSV file to a predefined output folder.

No data is stored at any point. No network access occurs. The script has no UI beyond the terminal.

---

## 2. Goals and Non-Goals

### Goals

- Parse machine-readable sampling protocol PDFs from two smelter templates (KV and BRX) in a layout-tolerant way.
- Filter deliveries by finalization date against a user-defined date range.
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

The script uses sequential `input()` prompts. All validation happens immediately after each entry. On invalid input, the same prompt is re-asked with an inline error message. The user can press `Ctrl+C` at any point to abort.

```
─────────────────────────────────────────────
  Delivery Protocol Analyzer
─────────────────────────────────────────────

  Configure this run:

  [1/4]  Output folder [/Users/jan/Documents/DeliveryReports]: ↵
         ✓ confirmed

  [2/4]  Protocols folder path: /Users/jan/Documents/Protocols
         ✓ Protocols/ found — 3 suppliers detected

  [3/4]  Date from (DD.MM.YYYY): 01.05.2026

  [4/4]  Date to   (DD.MM.YYYY): 31.05.2026

─────────────────────────────────────────────
  Ready to run
  Window:    01.05.2026 → 31.05.2026
  Suppliers: KK, BRX, NORDDEUTSCHE
  Output:    /Users/jan/Documents/DeliveryReports/
─────────────────────────────────────────────
  Press Enter to start or Ctrl+C to abort: ↵

  Processing...
```

### Prompt specifications

| Step | Prompt | Default | Validation | Re-prompt on failure |
|---|---|---|---|---|
| 1 | Output folder | Hardcoded constant at top of script | Path exists or can be created | Yes — show reason |
| 2 | Protocols folder path | None | Path exists, `Protocols/` subfolder present, at least one supplier subfolder present | Yes — show exact missing element |
| 3 | Date from | None | Parseable as DD.MM.YYYY, not in future | Yes — show format reminder |
| 4 | Date to | None | Parseable as DD.MM.YYYY, ≥ Date from | Yes — show reason |

After step 4, the script displays a confirmation summary (suppliers detected, date window, output path) and waits for a final Enter before execution begins. This is the last point at which the user can abort without side effects.

### Output folder default

A constant `OUTPUT_FOLDER` is defined at the top of `analyze.py`. The developer sets this once during installation. The user sees the current value at prompt [1/4] and can override it for a single run by typing a new path, or accept it with Enter.

If the output folder does not exist, the script creates it automatically.

---

## 5. Directory Structure Contract

### 5.1 Expected Folder Tree

```
{root}/
└── Protocols/
    └── {SupplierCode}/          ← e.g. KK, BRX  (one folder per smelter)
        └── {Year}/              ← e.g. 2026      (four-digit year)
            └── {DeliveryNumber}/← e.g. 56589     (numeric delivery ID)
                ├── Sampling protocol 56589A.pdf
                ├── Sampling protocol 56589B.pdf
                └── [other files — ignored silently]
```

`{root}` is the folder the user provides at prompt [2/4]. The script expects `Protocols/` as a direct child of root.

### 5.2 Naming Conventions

| Level | Format | Notes |
|---|---|---|
| Supplier folder | Alphanumeric string | Used verbatim as Smelter code in output. e.g. `KK`, `BRX` |
| Year folder | 4-digit integer | e.g. `2026`. Multiple year folders traversed when date range spans years. |
| Delivery folder | Numeric string | e.g. `56589`. Used as base delivery number in output. |
| Protocol PDF | Starts with `Sampling protocol` or `Sampling_protocol` (case-insensitive), ends with `.pdf` | Files not matching this pattern inside a delivery folder are silently ignored. |

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

This classification is based on the total count of matching PDFs in the folder, regardless of how many fall within the date window.

This distinction affects the output delivery number format — see Section 9.2.

---

## 6. PDF Specification

### 6.1 Two Templates

| Template ID | Issuer | Language |
|---|---|---|
| **KV** | KOVOHUTY, a.s. | English only |
| **BRX** | MONTANWERKE BRIXLEGG AKTIENGESELLSCHAFT | German + English bilingual |

**Parser strategy:** Anchor exclusively on English-language label strings. These are consistent across both templates. Do not rely on page coordinates, visual layout, or line order.

### 6.2 Fields Extracted

The script extracts exactly the following fields from each protocol PDF. No other fields are read.

| Field | English label anchor | Used for | Notes |
|---|---|---|---|
| Finalization date | `Date:` (last occurrence in document) | Date-window filtering + CSV output | Format: `DD.MM.YYYY` |
| Position number | `Pos.` | Delivery number construction + duplicate detection | Integer, e.g. `01`, `02` |
| Wet weight | `Wet weight [kg]:` | CSV output | European number format |
| Moisture | `Moisture [%]:` | CSV output | European number format |
| Dry weight | `Dry weight [kg]:` | CSV output + calculation base | European number format |
| Silver | `Ag` followed by value and `g/t` in Results section | Calculation | Optional — 0 if absent |
| Gold | `Au` followed by value and `g/t` in Results section | Calculation | Optional — 0 if absent |
| Palladium | `Pd` followed by value and `g/t` in Results section | Calculation | Optional — 0 if absent |
| Platinum | `Pt` followed by value and `g/t` in Results section | Calculation | Optional — 0 if absent |

**Fields explicitly ignored:**
- `Date of receipt:` — not extracted, not used anywhere.
- `Submission number:` / `Submisson number:` — not extracted, not used anywhere.
- Cu percentage — not extracted.
- Mixture / lot breakdown percentages — not extracted.
- Supplier name, contract number, material name, sample number, plate/container number — not extracted.

### 6.3 Finalization Date — Label Disambiguation

Every PDF contains two date-like fields:
- `Date of receipt:` — arrival date at smelter. **Ignored entirely.**
- `Date:` — finalization/signing date at bottom of document. **This is the one used.**

Since `Date of receipt:` also contains the word `Date`, the parser must take the **last match** of the pattern `Date:\s*\d{2}\.\d{2}\.\d{4}` in the full extracted text to reliably land on the finalization date.

### 6.4 Position Field

The `Pos.` field contains an integer (sometimes zero-padded: `01`, `02`). Parse as integer. Used to:
1. Construct the delivery number suffix in the output CSV.
2. Detect duplicate positions within a delivery folder.

Note: Kovohuty (KV) encodes the position in the filename letter suffix (A, B). Brixlegg (BRX) does not. The `Pos.` field inside the PDF is the authoritative source for position identification for both templates.

### 6.5 Number Format

All numeric values use European locale notation: dot = thousands separator, comma = decimal separator.

**Parsing rule:** Strip all `.` characters, replace `,` with `.`, then parse as float.

| PDF value | Parsed float |
|---|---|
| `14.520` | `14520.0` |
| `1.039,0000` | `1039.0` |
| `3,9700` | `3.97` |
| `22.145` | `22145.0` |
| `0,00` | `0.0` |

### 6.6 Extraction Strategy

Use `pdfplumber` to extract full page text as a single string. Apply regex patterns anchored to the English label strings defined above.

```python
import re

# Finalization date — take last match
re.findall(r"Date:\s*(\d{2}\.\d{2}\.\d{4})", text)[-1]

# Position number
re.search(r"Pos\.?\s*(\d+)", text)

# Wet weight
re.search(r"Wet weight \[kg\]:\s*([\d.,]+)", text, re.IGNORECASE)

# Moisture
re.search(r"Moisture \[%\]:\s*([\d.,]+)", text, re.IGNORECASE)

# Dry weight
re.search(r"Dry weight \[kg\]:\s*([\d.,]+)", text, re.IGNORECASE)

# Precious metals — only match value followed by g/t
re.search(r"\bAg\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
re.search(r"\bAu\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
re.search(r"\bPd\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
re.search(r"\bPt\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
```

The parser must tolerate variable whitespace between labels and values, and must function correctly when precious metal lines are absent.

---

## 7. Processing Pipeline

### 7.1 Algorithm

```
FUNCTION run(root_path, date_from, date_to):

  1. Validate root_path → Protocols/ → at least one supplier folder.
     Halt with specific error on any failure (see Section 11).

  2. suppliers = sorted subdirectories of Protocols/  (alphabetical)

  3. years_needed = all calendar years spanned by [date_from, date_to]

  4. result_rows = []
     excluded_log = []

  5. FOR each supplier in suppliers:
       FOR each year in years_needed:
         year_path = Protocols/{supplier}/{year}/
         IF year_path does not exist → skip silently

         delivery_folders = sorted subdirectories of year_path (ascending)

         FOR each delivery_folder in delivery_folders:

           protocol_files = files in delivery_folder matching naming pattern
                            (see Section 5.3), sorted ascending by filename

           IF len(protocol_files) == 0 → skip silently

           is_multi_position = len(protocol_files) > 1

           DUPLICATE CHECK (before processing any files):
             positions_seen = {}
             FOR each file in protocol_files:
               pos = extract Pos. field from PDF text
               IF pos in positions_seen:
                 HALT → ERROR_DUPLICATE_PROTOCOL
                        (report both file paths + delivery folder)
               positions_seen[pos] = file

           FOR each pdf_file in protocol_files:
             text = pdfplumber.extract_text(pdf_file)
             IF extraction fails → HALT → ERROR_FILE_UNREADABLE

             fin_date = parse finalization date
             IF parsing fails → HALT → ERROR_DATE_UNDETECTABLE

             IF fin_date NOT in [date_from, date_to]:
               excluded_log.append({file: pdf_file, date: fin_date, reason: "outside window"})
               CONTINUE  ← skip to next file, do not halt

             pos = parse Pos. field (integer)
             IF parsing fails → HALT → ERROR_POSITION_MISSING

             wet_weight = parse Wet weight [kg]
             moisture   = parse Moisture [%]
             dry_weight = parse Dry weight [kg]
             IF any of above fail → HALT → ERROR_WEIGHT_MISSING

             ag_gt = parse Ag g/t  (default 0 if absent)
             au_gt = parse Au g/t  (default 0 if absent)
             pd_gt = parse Pd g/t  (default 0 if absent)
             pt_gt = parse Pt g/t  (default 0 if absent)

             ag_kg = ag_gt * dry_weight / 1_000_000  (5 decimal places)
             au_kg = au_gt * dry_weight / 1_000_000
             pd_kg = pd_gt * dry_weight / 1_000_000
             pt_kg = pt_gt * dry_weight / 1_000_000

             IF is_multi_position:
               delivery_number = f"{delivery_folder}-{pos}"
             ELSE:
               delivery_number = delivery_folder

             result_rows.append({
               smelter_code:    supplier folder name,
               delivery_number: delivery_number,
               delivery_date:   fin_date,
               quantity_kg:     wet_weight,
               h2o_pct:         moisture,
               dry_quant_kg:    dry_weight,
               ag_kg, au_kg, pd_kg, pt_kg
             })

  6. SORT result_rows:
       primary:   smelter_code ascending (alphabetical)
       secondary: delivery_number ascending (natural sort on numeric base)
       tertiary:  position number ascending

  7. ASSIGN Lp: sequential integer starting at 1

  8. COMPUTE totals row (see Section 8.2)

  9. WRITE CSV (see Section 9)

  10. PRINT run summary to terminal (see Section 10)
```

### 7.2 Date Range and Year Traversal

- Both `date_from` and `date_to` are inclusive.
- If the date range spans two calendar years (e.g. `15.12.2025` → `15.01.2026`), the script must look inside both `2025/` and `2026/` year folders for every supplier.
- The date used for filtering is always the finalization date (`Date:`) from the PDF — never the file system modification date, never `Date of receipt`.

### 7.3 Duplicate Detection

A duplicate is defined as: two or more PDF files within the same delivery folder whose `Pos.` field value resolves to the same integer.

Duplicate detection runs before any file in that delivery folder is processed. On detection: halt immediately, report both conflicting file paths and the delivery folder path, do not write any output.

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
| 3 | `Delivery date` | PDF `Date:` (finalization date) | String | `DD.MM.YYYY` |
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

```
  [OK]  KK / 2026 / 56589-1  →  finalized 15.05.2026
  [OK]  KK / 2026 / 56589-2  →  finalized 15.05.2026
  [--]  KK / 2026 / 57100-1  →  finalized 12.04.2026  (outside window)
  [OK]  BRX / 2026 / 26002658-1  →  finalized 22.05.2026
```

- `[OK]` — protocol extracted and included in results.
- `[--]` — protocol detected, finalization date outside window, excluded from results.
- `[ERR]` — error encountered (see Section 11). Followed by halt.

### 10.2 Run Summary (on success)

Printed after the CSV is written:

```
─────────────────────────────────────────────
  Run complete
─────────────────────────────────────────────
  Protocols processed:   23
  Deliveries included:   12
  Protocols excluded:     5  (outside window — see above)

  Output written to:
  /Users/jan/Documents/DeliveryReports/DeliveryReport_01052026_31052026.csv
─────────────────────────────────────────────
```

"Protocols processed" = total PDFs that matched the naming pattern and were opened.
"Deliveries included" = count of unique delivery folder names that contributed at least one row.
"Protocols excluded" = PDFs opened successfully but whose finalization date fell outside the window.

### 10.3 Error Output (on halt)

```
─────────────────────────────────────────────
  [ERR]  Run halted — duplicate protocol detected

  Delivery folder:
    /Users/jan/Documents/Protocols/KK/2026/56589/

  Conflicting files:
    Sampling protocol 56589A.pdf  (Pos. 01)
    Sampling protocol 56589C.pdf  (Pos. 01)

  Both files claim position 01. Remove or rename the
  duplicate before rerunning.
─────────────────────────────────────────────
  No output file was written.
─────────────────────────────────────────────
```

No partial CSV is ever written on error. The output file either exists and is complete, or does not exist.

---

## 11. Error Catalog

All errors halt execution immediately. No partial results are written.

### Structure and Path Errors

| Code | Trigger | Message shown |
|---|---|---|
| `E01` | Root path does not exist or is not a directory | `Path not found: {path}. Please enter a valid folder path.` |
| `E02` | `Protocols/` folder missing inside root | `"Protocols" folder not found inside {root}. Expected: {root}/Protocols/` |
| `E03` | No supplier subfolders found inside `Protocols/` | `No supplier folders found inside Protocols/. The folder appears to be empty.` |

### File Errors

| Code | Trigger | Message shown |
|---|---|---|
| `E04` | PDF cannot be opened or yields no extractable text | `Cannot read file: {path}. File may be corrupted, password-protected, or a scanned image.` |
| `E05` | Two files in same delivery folder share the same Pos. value | `Duplicate position detected in {delivery_folder}. Files: {file1} and {file2} both claim Pos. {n}. Remove the duplicate and rerun.` |

### Data Extraction Errors

| Code | Trigger | Message shown |
|---|---|---|
| `E06` | Finalization date cannot be parsed from PDF text | `Cannot extract finalization date from: {path}. File was read but no valid date found. Verify the file manually.` |
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
