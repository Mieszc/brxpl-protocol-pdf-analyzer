"""
Delivery Protocol Analyzer

This script automates the parsing and analysis of supplier delivery/sampling protocols in PDF format.
It uses pdfplumber to extract text and regular expressions to parse key metrics, outputting 
them into an Excel-ready semicolon-delimited CSV spreadsheet.

SAFE ARCHITECTURE & THE 2-FOLDER CONTRACT:
1. Master Folder (MASTER_FOLDER): Read-only baseline database containing the original PDFs.
   The script never modifies, moves, or deletes any files in this folder.
2. Output Folder (OUTPUT_FOLDER): The destination directory for final CSV reports.
"""

import sys
import csv
import pathlib
import datetime
import re
import os
import shutil

# Verify that external dependencies are installed. Rich is used for terminal output formatting,
# and pdfplumber is used to extract textual layout data from PDF documents.
try:
    from rich.console import Console
    from rich.markup import escape
    import pdfplumber
except ImportError:
    print("Błąd: Brakujące zależności. Uruchom 'pip install -r requirements.txt'")
    sys.exit(1)

# ---------------------------------------------------------
# PATH CONFIGURATION
# ---------------------------------------------------------
# Default folders for workspace operations. These can be adjusted by the user as needed.
OUTPUT_FOLDER = "/Users/MIESZKO/Desktop/mlabsai-work-projects/clients/brxpl-spzoo/output-protocols-analyzed"
MASTER_FOLDER = "/Users/MIESZKO/Desktop/brxpl/Dostawcy"

# Initialize the Rich console object for colorized/formatted terminal stdout prints
console = Console()

def check_write_permission(dir_path):
    """
    Checks if a directory is writable by attempting to create it if it doesn't 
    exist, and then touching/deleting a temporary test file inside it.
    
    Returns:
        bool: True if writable/creatable, False otherwise.
    """
    path = pathlib.Path(dir_path)
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception:
            return False
    test_file = path / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
        return True
    except Exception:
        return False

def find_supplier_dirs(base_dir):
    """
    Finds supplier directories by traversing the directory tree.
    It only traverses directories, and avoids descending into 4-digit year folders.
    This prevents scanning files and deep delivery subdirectories, which is extremely
    slow on network drives (e.g., WebDAV over VPN).
    """
    supplier_dirs = set()
    queue = [pathlib.Path(base_dir)]
    
    while queue:
        current_dir = queue.pop(0)
        try:
            subdirs = []
            has_year_subdir = False
            for entry in current_dir.iterdir():
                if entry.is_dir():
                    if re.match(r"^\d{4}$", entry.name):
                        has_year_subdir = True
                    else:
                        subdirs.append(entry)
            if has_year_subdir:
                supplier_dirs.add(current_dir)
            else:
                queue.extend(subdirs)
        except Exception:
            pass
            
    return sorted(list(supplier_dirs), key=lambda x: x.name)

def run_preflight_checks():
    """
    Validates directories and permissions before beginning execution.
    Halts the script immediately on failure to prevent runtime crashes.
    
    Checks:
    - Master folder exists, is a directory, and contains subfolders (is not empty).
    - Output folder is writable.
    """
    console.print("  Uruchamianie wstępnych testów bezpieczeństwa...")
    
    # 1. Verify that the Master directory exists
    master_path = pathlib.Path(MASTER_FOLDER)
    if not master_path.exists() or not master_path.is_dir():
        console.print(f"[bold red][ERR] Brakujący lub nieprawidłowy folder główny (Master): {escape(str(MASTER_FOLDER))}[/bold red]")
        sys.exit(1)
        
    # 2. Verify that the Master directory is not empty
    try:
        next(master_path.iterdir())
    except StopIteration:
        console.print(f"[bold red][ERR] Folder główny (Master) jest pusty: {escape(str(MASTER_FOLDER))}. Musi on zawierać oryginalne pliki bazy danych.[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red][ERR] Nie można odczytać folderu głównego (Master): {escape(str(e))}[/bold red]")
        sys.exit(1)
        
    # 3. Ensure the Output folder is writable to safely write the CSV report later
    if not check_write_permission(OUTPUT_FOLDER):
        console.print(f"[bold red][ERR] Brak uprawnień do zapisu w folderze wyjściowym (Output): {escape(str(OUTPUT_FOLDER))}[/bold red]")
        sys.exit(1)
        
    console.print("         [green]✓[/green] Wstępne testy bezpieczeństwa zakończone pomyślnie.\n")

def parse_number(val_str):
    """
    Parses a string representing a decimal number into a float.
    Handles European formatting where '.' is a thousands separator and ',' is 
    the decimal separator (e.g., '23.080,000' -> 23080.0, or '3,63' -> 3.63).
    
    Args:
        val_str (str): The raw string extracted from the PDF.
        
    Returns:
        float: The parsed float value, defaulting to 0.0 on ValueError.
    """
    if not val_str:
        return 0.0
    val_str = val_str.replace('.', '')  # Remove thousands separators
    val_str = val_str.replace(',', '.')  # Standardize decimal point to Python float format
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def prompt_date(prompt_text):
    """
    Prompts the user in the terminal to enter a date in DD.MM.YYYY format.
    Validates that the input represents a valid date and is not in the future.
    
    Args:
        prompt_text (str): The text message shown to the user.
        
    Returns:
        datetime.date: The validated date object.
    """
    while True:
        console.print(prompt_text, end="")
        date_str = input().strip()
        try:
            dt = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
            if dt > datetime.date.today():
                console.print(f"         [red]Data nie może być z przyszłości. Dzisiejsza data to {datetime.date.today().strftime('%d.%m.%Y')}[/red]\n")
                continue
            return dt
        except ValueError:
            console.print("         [red]Nieprawidłowy format daty. Użyj formatu DD.MM.YYYY[/red]\n")

def extract_pdf_data(pdf_path):
    """
    Extracts relevant delivery metadata, weights, and precious metal rates 
    from a single PDF document.
    
    The layout parser is designed to handle multiple languages (EN, DE, SK)
    and is resilient to OCR accent loss or spacing variation:
    - Accent variations (e.g., 'á', 'ť', 'č', 'š') are supported using regex classes.
    - Key weight fields ('Wet weight', 'Moisture', 'Dry weight') are mapped to synonyms.
    - Precious metals (Ag, Au, Pd, Pt) are matched on their element code followed by 'g/t'.
    
    Args:
        pdf_path (pathlib.Path): Absolute path to the PDF file.
        
    Returns:
        tuple: (data_dict, error_string)
               - If success: (dict with values, None)
               - If failure: (None, error description string)
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        return None, f"Nie można otworzyć lub odczytać pliku PDF: {str(e)}"

    # 1. Date of receipt extraction
    # The primary check searches for specific labels denoting receiving date in three languages.
    receipt_date_str = None
    label_matches = re.findall(
        r"(?:Date of receipt|Eingangsdatum|D[aá]tum prijatia|D[aá]tum dodania|D[aá]tum doru[cč]enia)\s*:\s*(\d{2}\.\d{2}\.\d{4})", 
        text, re.IGNORECASE
    )
    if label_matches:
        receipt_date_str = label_matches[0]
    else:
        # Fallback check: extract the first date matching DD.MM.YYYY pattern found in the document text.
        # This acts as an emergency default when receiving-date labels are missing or formatted oddly.
        fallback_matches = re.findall(r"\b(\d{2}\.\d{2}\.\d{4})\b", text)
        if fallback_matches:
            receipt_date_str = fallback_matches[0]
            
    if not receipt_date_str:
        return None, "Brak lub nieczytelna data dostawy/otrzymania"
    
    # 2. Position extraction
    # Matches patterns like 'Pos. 01' or 'Pos 1' to derive the multi-delivery split ranking.
    pos_match = re.search(r"Pos\.?\s*(\d+)", text)
    if not pos_match:
        return None, "Brak lub nieczytelny numer pozycji (Pos.)"
    pos = int(pos_match.group(1))

    # 3. Weight fields extraction
    # Match wet weight: Wet weight, Nassgewicht (DE), mokrá/vlhká hmotnosť (SK), Feuchtgewicht, or hmotnosť za mokra
    # Allows optional unit '[kg]' and arbitrary whitespace before the colon.
    ww_match = re.search(
        r"(?:Wet[ \t]*weight|Nassgewicht|mokr[aá][ \t]*hmotnos[tť]|vlhk[aá][ \t]*hmotnos[tť]|Feuchtgewicht|hmotnos[tť][ \t]*za[ \t]*mokra)"
        r"(?:[ \t]*\[?kg\]?)?[ \t]*:[ \t]*([\d.,]+)",
        text, re.IGNORECASE
    )
    if not ww_match:
        return None, "Brak pola wagi mokrej Wet weight [kg]"
    wet_weight = parse_number(ww_match.group(1))
    if wet_weight <= 0.0:
        return None, f"Nieprawidłowa waga mokra: {wet_weight}"

    # Moisture percentage (H2O): Moisture, Nässe (DE), Feuchtigkeit (DE), Feuchte, or vlhkosť (SK)
    # Allows optional unit '[%]' and arbitrary whitespace. Default to 0.0 if omitted.
    moisture = 0.0
    m_match = re.search(
        r"(?:Moisture|N[aä]sse|Feuchtigkeit|Feuchte|vlhkos[tť])"
        r"(?:[ \t]*\[?%\]?)?[ \t]*:[ \t]*([\d.,]+)",
        text, re.IGNORECASE
    )
    if m_match:
        moisture = parse_number(m_match.group(1))

    # Match dry weight: Dry weight, Trockengewicht (DE), suchá hmotnosť (SK), sušina (SK), or hmotnosť za sucha
    dw_match = re.search(
        r"(?:Dry[ \t]*weight|Trockengewicht|such[aá][ \t]*hmotnos[tť]|su[sš]ina|hmotnos[tť][ \t]*za[ \t]*sucha)"
        r"(?:[ \t]*\[?kg\]?)?[ \t]*:[ \t]*([\d.,]+)",
        text, re.IGNORECASE
    )
    if not dw_match:
        return None, "Brak pola wagi suchej Dry weight [kg]"
    dry_weight = parse_number(dw_match.group(1))
    if dry_weight <= 0.0:
        return None, f"Invalid Dry weight: {dry_weight}"

    # 4. Precious metals (g/t - grams per metric ton) extraction
    ag = au = pd = pt = 0.0
    ag_match = re.search(r"\bAg\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
    if ag_match: ag = parse_number(ag_match.group(1))
    
    au_match = re.search(r"\bAu\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
    if au_match: au = parse_number(au_match.group(1))
    
    pd_match = re.search(r"\bPd\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
    if pd_match: pd = parse_number(pd_match.group(1))
    
    pt_match = re.search(r"\bPt\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
    if pt_match: pt = parse_number(pt_match.group(1))
    
    # Validate date format to date object conversion
    try:
        dt = datetime.datetime.strptime(receipt_date_str, "%d.%m.%Y").date()
    except:
        return None, f"Nieprawidłowy format daty: {receipt_date_str}"

    return {
        "date_dt": dt,
        "date_str": receipt_date_str,
        "pos": pos,
        "wet_weight": wet_weight,
        "moisture": moisture,
        "dry_weight": dry_weight,
        "ag_gt": ag,
        "au_gt": au,
        "pd_gt": pd,
        "pt_gt": pt
    }, None

def main():
    try:
        console.print("─────────────────────────────────────────────")
        console.print("  Delivery Protocol Analyzer (Analizator Protokołów)")
        console.print("─────────────────────────────────────────────\n")
        
        # 1. Run Preflight checks (folder existences, folder emptiness, write permissions)
        run_preflight_checks()

        console.print("  Konfiguracja uruchomienia:\n")
        console.print(f"  \\[1/3]  Folder wyjściowy (Output) \\[{escape(str(OUTPUT_FOLDER))}]: ↵\n         [green]✓[/green] potwierdzono\n")
        
        # 2. Prompt for date filter window
        date_from = prompt_date("  [2/3]  Data od (DD.MM.YYYY): ")
        date_to = prompt_date("  [3/3]  Data do (DD.MM.YYYY): ")
        
        if date_to < date_from:
            console.print("[bold red]Data końcowa (do) musi być późniejsza lub równa dacie początkowej (od). Przerwano.[/bold red]")
            sys.exit(1)

        # 3. Confirm start with summary info
        console.print("─────────────────────────────────────────────")
        console.print("  Gotowy do uruchomienia")
        console.print(f"  Zakres:    {date_from.strftime('%d.%m.%Y')} → {date_to.strftime('%d.%m.%Y')}")
        console.print(f"  Zapis do:  {escape(str(OUTPUT_FOLDER))}")
        console.print("─────────────────────────────────────────────")
        console.print("  Naciśnij Enter, aby rozpocząć, lub Ctrl+C, aby anulować: ", end="")
        input()
        console.print("  Przetwarzanie...\n")

        master_dir = pathlib.Path(MASTER_FOLDER)
            
        result_rows = []
        protocols_processed = 0
        protocols_excluded = 0
        protocols_failed = 0
        deliveries_included = set()
        
        # 4. Dynamically discover supplier directories inside the Master folder.
        # Uses an optimized directory-only BFS traversal to avoid scanning deep files/folders
        # over slow network connections (like WebDAV/VPN).
        supplier_dirs = find_supplier_dirs(master_dir)

        # Determine which calendar years are spanned by the requested date range
        years_needed = set(range(date_from.year, date_to.year + 1))

        # 5. Traverse files using standard schema: Supplier -> Year -> Month -> Delivery
        for supplier_dir in supplier_dirs:
            # Match 4-digit Year directory names that fall within the needed years
            for year_dir in sorted(d for d in supplier_dir.iterdir() if d.is_dir() and re.match(r"^\d{4}$", d.name) and int(d.name) in years_needed):
                
                # Determine which months are valid for this year to narrow traversal
                year_val = int(year_dir.name)
                if year_val == date_from.year and year_val == date_to.year:
                    valid_months = set(range(date_from.month, date_to.month + 1))
                elif year_val == date_from.year:
                    valid_months = set(range(date_from.month, 13))
                elif year_val == date_to.year:
                    valid_months = set(range(1, date_to.month + 1))
                else:
                    valid_months = set(range(1, 13))

                # Match 2-digit Month directory names that fall within the valid months
                for month_dir in sorted(d for d in year_dir.iterdir() if d.is_dir() and re.match(r"^\d{2}$", d.name) and int(d.name) in valid_months):
                    # Traverse individual Delivery subdirectories
                    for delivery_dir in sorted(d for d in month_dir.iterdir() if d.is_dir()):
                        
                        # Gather all files in the delivery directory with '.pdf' extension containing 'sampling protocol' (case insensitive)
                        pdf_files = [f for f in delivery_dir.iterdir() if f.is_file() and f.suffix.lower() == '.pdf' and 'sampling protocol' in f.name.lower()]
                        if not pdf_files:
                            continue
                            
                        # PRE-PROCESS: Check for duplicate delivery position numbers.
                        # Having multiple files claim the same position (e.g., two PDFs with "Pos. 01") inside the same delivery
                        # directory violates data integrity and triggers a safety halt.
                        positions_seen = {}
                        pdfs_to_process = []
                        for pdf in sorted(pdf_files):
                            data, err_reason = extract_pdf_data(pdf)
                            if err_reason:
                                # Non-halting fail-safe strategy: Log failure and continue processing remaining PDFs.
                                console.print(f"  [red][FAIL][/red] {escape(supplier_dir.name)} / {escape(year_dir.name)} / {escape(pdf.name)}  →  [red]{escape(err_reason)}[/red]")
                                protocols_failed += 1
                                protocols_processed += 1
                                continue

                            pos = data['pos']
                            if pos in positions_seen:
                                # Halting safety check: halt if duplicate positions are detected within a single delivery directory.
                                console.print(f"\n[bold red][ERR] Uruchomienie przerwane — wykryto zduplikowany protokół[/bold red]")
                                console.print(f"  Katalog dostawy: {escape(str(delivery_dir))}")
                                console.print(f"  Konfliktujące pliki: {escape(positions_seen[pos].name)} oraz {escape(pdf.name)} oba zgłaszają pozycję Pos. {pos}")
                                sys.exit(1)
                            positions_seen[pos] = pdf
                            pdfs_to_process.append((pdf, data))
                                
                        is_multi_position = len(pdf_files) > 1
                        
                        # 6. Derive Smelter Code (BRX/Brixlegg or KK/Kovohuty)
                        # Rule: If the delivery folder name begins with the last 2 digits of the Year folder (e.g. '26' for Year 2026),
                        # the smelter code is 'BRX'. Otherwise, it defaults to 'KK'.
                        year_str = year_dir.name
                        year_prefix = year_str[-2:] if len(year_str) >= 2 else ""
                        
                        if delivery_dir.name.startswith(year_prefix):
                            smelter_code = 'BRX'
                        else:
                            smelter_code = 'KK'
                            
                        # 7. Process files that parsed successfully
                        for pdf, data in pdfs_to_process:
                            protocols_processed += 1
                            
                            # Filter based on the selected Date Window
                            if not (date_from <= data['date_dt'] <= date_to):
                                protocols_excluded += 1
                                console.print(f"  \\[--]  {escape(supplier_dir.name)} / {escape(year_dir.name)} / {escape(delivery_dir.name)}  →  otrzymano {data['date_str']}  (poza zakresem)")
                                continue
                                
                            # If there are multiple positions, append the position suffix (e.g., DeliveryName-1)
                            delivery_number = f"{delivery_dir.name}-{data['pos']}" if is_multi_position else delivery_dir.name
                            deliveries_included.add(delivery_dir.name)
                            
                            # Calculate precious metal content in kilograms: (g/t * Dry Weight kg) / 1,000,000
                            # Rounded to 5 decimal places.
                            ag_kg = round((data['ag_gt'] * data['dry_weight']) / 1000000.0, 5)
                            au_kg = round((data['au_gt'] * data['dry_weight']) / 1000000.0, 5)
                            pd_kg = round((data['pd_gt'] * data['dry_weight']) / 1000000.0, 5)
                            pt_kg = round((data['pt_gt'] * data['dry_weight']) / 1000000.0, 5)
                            
                            result_rows.append({
                                'smelter_code': smelter_code,
                                'delivery_number': delivery_number,
                                'pos': data['pos'],
                                'delivery_date': data['date_str'],
                                'quantity_kg': round(data['wet_weight'], 3),
                                'h2o_pct': round(data['moisture'], 2),
                                'dry_quant_kg': round(data['dry_weight'], 3),
                                'ag_kg': ag_kg,
                                'au_kg': au_kg,
                                'pd_kg': pd_kg,
                                'pt_kg': pt_kg
                            })
                            console.print(f"  \\[OK]  {escape(supplier_dir.name)} / {escape(year_dir.name)} / {escape(delivery_number)}  →  otrzymano {data['date_str']}")

        # 8. SORTING: Sort result rows
        # Primary: Smelter Code (BRX first, then KK)
        # Secondary: Numeric representation of delivery folder name (lowest to highest)
        # Tertiary: Position (Pos.) number
        def get_sort_key(x):
            base_str = x['delivery_number'].split('-')[0]
            try:
                base_val = int(base_str)
            except ValueError:
                base_val = base_str  # Fallback to string comparison if not numeric
            return (x['smelter_code'], base_val, x['pos'])

        result_rows.sort(key=get_sort_key)
        
        # 9. EXCEL COMPATIBILITY CSV GENERATION
        out_folder = pathlib.Path(OUTPUT_FOLDER)
        out_folder.mkdir(parents=True, exist_ok=True)
        out_name = f"DeliveryReport_{date_from.strftime('%d%m%Y')}_{date_to.strftime('%d%m%Y')}.csv"
        out_path = out_folder / out_name
        
        # Prevent overwriting of existing reports by appending a counter suffix (e.g. _2, _3)
        counter = 2
        while out_path.exists():
            out_name = f"DeliveryReport_{date_from.strftime('%d%m%Y')}_{date_to.strftime('%d%m%Y')}_{counter}.csv"
            out_path = out_folder / out_name
            counter += 1

        if result_rows:
            with open(out_path, 'w', encoding='utf-8', newline='') as csvfile:
                fieldnames = ['Lp', 'Delivery number', 'Delivery date', 'Smelter code', 'Quantity kg', 'H2O[%]', 'Dry quant. kg', 'Ag kg', 'Au kg', 'Pd kg', 'Pt kg']
                # Semicolon delimiter ensures direct loading in European regional versions of Excel
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                tot_q = tot_d = tot_ag = tot_au = tot_pd = tot_pt = 0.0
                
                for idx, row in enumerate(result_rows, 1):
                    # Replace dots with commas for decimal points to support regional Excel localization
                    writer.writerow({
                        'Lp': idx,
                        'Delivery number': row['delivery_number'],
                        'Delivery date': row['delivery_date'],
                        'Smelter code': row['smelter_code'],
                        'Quantity kg': f"{row['quantity_kg']:.3f}".replace('.', ','),
                        'H2O[%]': f"{row['h2o_pct']:.2f}".replace('.', ','),
                        'Dry quant. kg': f"{row['dry_quant_kg']:.3f}".replace('.', ','),
                        'Ag kg': f"{row['ag_kg']:.5f}".replace('.', ','),
                        'Au kg': f"{row['au_kg']:.5f}".replace('.', ','),
                        'Pd kg': f"{row['pd_kg']:.5f}".replace('.', ','),
                        'Pt kg': f"{row['pt_kg']:.5f}".replace('.', ',')
                    })
                    
                    tot_q += row['quantity_kg']
                    tot_d += row['dry_quant_kg']
                    tot_ag += row['ag_kg']
                    tot_au += row['au_kg']
                    tot_pd += row['pd_kg']
                    tot_pt += row['pt_kg']
                    
                # Write Totals Row at the bottom of the CSV
                writer.writerow({
                    'Lp': 'Total:',
                    'Delivery number': '',
                    'Delivery date': '',
                    'Smelter code': '',
                    'Quantity kg': f"{round(tot_q, 3):.3f}".replace('.', ','),
                    'H2O[%]': '',
                    'Dry quant. kg': f"{round(tot_d, 3):.3f}".replace('.', ','),
                    'Ag kg': f"{round(tot_ag, 5):.5f}".replace('.', ','),
                    'Au kg': f"{round(tot_au, 5):.5f}".replace('.', ','),
                    'Pd kg': f"{round(tot_pd, 5):.5f}".replace('.', ','),
                    'Pt kg': f"{round(tot_pt, 5):.5f}".replace('.', ',')
                })

        console.print("─────────────────────────────────────────────")
        console.print("  Analiza zakończona")
        console.print("─────────────────────────────────────────────")
        console.print(f"  Przetworzone protokoły:  {protocols_processed}")
        console.print(f"  Uwzględnione dostawy:    {len(deliveries_included)}")
        console.print(f"  Wykluczone protokoły:    {protocols_excluded}")
        console.print(f"  Nieudane protokoły:      {protocols_failed}\n")
        
        # Zero matches safeguard
        if not result_rows:
            console.print("─────────────────────────────────────────────")
            console.print("[yellow][WARN] Nie znaleziono pasujących protokołów w wybranym zakresie dat.[/yellow]")
            console.print("  Raport nie został wygenerowany.")
            console.print("─────────────────────────────────────────────")
            return

        console.print("  Raport zapisano w:")
        console.print(f"  {out_path}", markup=False)
        console.print("─────────────────────────────────────────────")

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Uruchomienie przerwane przez użytkownika.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red][ERR] Nieoczekiwany błąd: {escape(str(e))}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
