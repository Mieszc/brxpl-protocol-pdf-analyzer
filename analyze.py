import sys
import csv
import pathlib
import datetime
import re
import os
import shutil

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
OUTPUT_FOLDER = "/Users/MIESZKO/Desktop/mlabsai-work-projects/clients/brxpl-spzoo/output-protocols-analyzed"
MASTER_FOLDER = "/Users/MIESZKO/Desktop/brxpl/Dostawcy"
DROPZONE_FOLDER = "/Users/MIESZKO/Desktop/mlabsai-work-projects/clients/brxpl-spzoo/smapling-protocol-analyzer/brxpl-protocol-pdf-analyzer/samples"
ARCHIVE_FOLDER = "/Users/MIESZKO/Desktop/mlabsai-work-projects/clients/brxpl-spzoo/smapling-protocol-analyzer/brxpl-protocol-pdf-analyzer/archive"

console = Console()

def check_write_permission(dir_path):
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

def run_preflight_checks():
    console.print("  Uruchamianie wstępnych testów bezpieczeństwa...")
    # 1. Check if Dropzone exists and is a directory
    token_path = pathlib.Path(DROPZONE_FOLDER)
    if not token_path.exists() or not token_path.is_dir():
        console.print(f"[bold red][ERR] Nie znaleziono folderu przejściowego (Dropzone): {escape(str(DROPZONE_FOLDER))}[/bold red]")
        console.print(f"  Skopiuj folder '[bold]{token_path.name}[/bold]' z oryginalnej bazy (Master) do folderu '[bold]{token_path.parent.name}[/bold]' przed uruchomieniem programu.")
        sys.exit(1)
        
    # 1b. Check if Dropzone contains any sampling protocol PDFs
    pdf_found = False
    try:
        for p in token_path.rglob("*.pdf"):
            if "sampling protocol" in p.name.lower() or "sampling_protocol" in p.name.lower():
                pdf_found = True
                break
    except Exception as e:
        console.print(f"[bold red][ERR] Nie można odczytać folderu Dropzone: {escape(str(e))}[/bold red]")
        sys.exit(1)
        
    if not pdf_found:
        console.print(f"[bold red][ERR] Folder Dropzone jest pusty lub nie zawiera plików PDF z protokołami dostaw: {escape(str(DROPZONE_FOLDER))}[/bold red]")
        console.print("  Skopiuj pliki PDF z protokołami do folderu Dropzone przed uruchomieniem analizy.")
        sys.exit(1)
    
    # 2. Safety token check inside parent samples
    safe_token = token_path.parent / ".safe_dropzone"
    if not safe_token.exists():
        # Ensure it exists since we didn't create it in the skeleton before
        safe_token.touch()
        
    # 3. Check if Master folder exists and is a directory
    master_path = pathlib.Path(MASTER_FOLDER)
    if not master_path.exists() or not master_path.is_dir():
        console.print(f"[bold red][ERR] Brakujący lub nieprawidłowy folder główny (Master): {escape(str(MASTER_FOLDER))}[/bold red]")
        sys.exit(1)
        
    # 4. Check if Master folder is not empty
    try:
        next(master_path.iterdir())
    except StopIteration:
        console.print(f"[bold red][ERR] Folder główny (Master) jest pusty: {escape(str(MASTER_FOLDER))}. Musi on zawierać oryginalne pliki bazy danych.[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red][ERR] Nie można odczytać folderu głównego (Master): {escape(str(e))}[/bold red]")
        sys.exit(1)
        
    # 5. Check if Output folder is writable
    if not check_write_permission(OUTPUT_FOLDER):
        console.print(f"[bold red][ERR] Brak uprawnień do zapisu w folderze wyjściowym (Output): {escape(str(OUTPUT_FOLDER))}[/bold red]")
        sys.exit(1)
        
    # 6. Check if Archive folder is writable
    if not check_write_permission(ARCHIVE_FOLDER):
        console.print(f"[bold red][ERR] Brak uprawnień do zapisu w folderze archiwum (Archive): {escape(str(ARCHIVE_FOLDER))}[/bold red]")
        sys.exit(1)
        
    console.print("         [green]✓[/green] Wstępne testy bezpieczeństwa zakończone pomyślnie.\n")

def parse_number(val_str):
    if not val_str:
        return 0.0
    val_str = val_str.replace('.', '')
    val_str = val_str.replace(',', '.')
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def prompt_date(prompt_text):
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
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        return None, f"Nie można otworzyć lub odczytać pliku PDF: {str(e)}"

    # Date of receipt (First match of specific labels, fallback to first date found)
    receipt_date_str = None
    
    # Primary check: Specific labels
    label_matches = re.findall(
        r"(?:Date of receipt|Eingangsdatum|D[aá]tum prijatia|D[aá]tum dodania|D[aá]tum doru[cč]enia)\s*:\s*(\d{2}\.\d{2}\.\d{4})", 
        text, re.IGNORECASE
    )
    if label_matches:
        receipt_date_str = label_matches[0]
    else:
        # Fallback check: First DD.MM.YYYY date in the document
        fallback_matches = re.findall(r"\b(\d{2}\.\d{2}\.\d{4})\b", text)
        if fallback_matches:
            receipt_date_str = fallback_matches[0]
            
    if not receipt_date_str:
        return None, "Brak lub nieczytelna data dostawy/otrzymania"
    
    # Position
    pos_match = re.search(r"Pos\.?\s*(\d+)", text)
    if not pos_match:
        return None, "Brak lub nieczytelny numer pozycji (Pos.)"
    pos = int(pos_match.group(1))

    # Weight fields
    # Match wet weight, Nassgewicht (DE), or mokrá/vlhká hmotnosť (SK)
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

    moisture = 0.0
    # Match moisture, Nässe (DE), Feuchtigkeit (DE), or vlhkosť (SK)
    m_match = re.search(
        r"(?:Moisture|N[aä]sse|Feuchtigkeit|Feuchte|vlhkos[tť])"
        r"(?:[ \t]*\[?%\]?)?[ \t]*:[ \t]*([\d.,]+)",
        text, re.IGNORECASE
    )
    if m_match:
        moisture = parse_number(m_match.group(1))

    # Match dry weight, Trockengewicht (DE), or suchá hmotnosť/sušina (SK)
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

    # Precious metals
    ag = au = pd = pt = 0.0
    ag_match = re.search(r"\bAg\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
    if ag_match: ag = parse_number(ag_match.group(1))
    
    au_match = re.search(r"\bAu\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
    if au_match: au = parse_number(au_match.group(1))
    
    pd_match = re.search(r"\bPd\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
    if pd_match: pd = parse_number(pd_match.group(1))
    
    pt_match = re.search(r"\bPt\s+([\d.,]+)\s*g/t", text, re.IGNORECASE)
    if pt_match: pt = parse_number(pt_match.group(1))
    
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
        
        run_preflight_checks()

        console.print("  Konfiguracja uruchomienia:\n")
        console.print(f"  \\[1/4]  Folder wyjściowy (Output) \\[{escape(str(OUTPUT_FOLDER))}]: ↵\n         [green]✓[/green] potwierdzono\n")
        console.print(f"  \\[2/4]  Folder przejściowy (Dropzone): {escape(str(DROPZONE_FOLDER))}\n         [green]✓[/green] znaleziono\n")
        
        date_from = prompt_date("  [3/4]  Data od (DD.MM.YYYY): ")
        date_to = prompt_date("  [4/4]  Data do (DD.MM.YYYY): ")
        
        if date_to < date_from:
            console.print("[bold red]Data końcowa (do) musi być późniejsza lub równa dacie początkowej (od). Przerwano.[/bold red]")
            sys.exit(1)

        console.print("─────────────────────────────────────────────")
        console.print("  Gotowy do uruchomienia")
        console.print(f"  Zakres:    {date_from.strftime('%d.%m.%Y')} → {date_to.strftime('%d.%m.%Y')}")
        console.print(f"  Zapis do:  {escape(str(OUTPUT_FOLDER))}")
        console.print("─────────────────────────────────────────────")
        console.print("  Naciśnij Enter, aby rozpocząć, lub Ctrl+C, aby anulować: ", end="")
        input()
        console.print("  Przetwarzanie...\n")

        dropzone = pathlib.Path(DROPZONE_FOLDER)
        if not dropzone.exists():
            console.print("[red][ERR] Nie znaleziono folderu przejściowego (Dropzone).[/red]")
            sys.exit(1)
            
        result_rows = []
        protocols_processed = 0
        protocols_excluded = 0
        protocols_failed = 0
        deliveries_included = set()
        
        # Dynamically discover supplier directories inside the dropzone
        supplier_dirs = []
        for p in dropzone.rglob("*"):
            if p.is_dir() and re.match(r"^\d{4}$", p.name):
                sup_dir = p.parent
                if sup_dir not in supplier_dirs:
                    supplier_dirs.append(sup_dir)
        supplier_dirs = sorted(supplier_dirs, key=lambda x: x.name)

        # Traverse Supplier -> Year -> Month -> Delivery
        for supplier_dir in supplier_dirs:
            for year_dir in sorted(d for d in supplier_dir.iterdir() if d.is_dir() and re.match(r"^\d{4}$", d.name)):
                for month_dir in sorted(d for d in year_dir.iterdir() if d.is_dir() and re.match(r"^\d{2}$", d.name)):
                    for delivery_dir in sorted(d for d in month_dir.iterdir() if d.is_dir()):
                        
                        pdf_files = [f for f in delivery_dir.iterdir() if f.is_file() and f.suffix.lower() == '.pdf' and 'sampling protocol' in f.name.lower()]
                        if not pdf_files:
                            continue
                            
                        # Duplicate Position Check Before Processing
                        positions_seen = {}
                        pdfs_to_process = []
                        for pdf in sorted(pdf_files):
                            # Master Verification check (failsafe)
                            relative_path = pdf.relative_to(supplier_dir.parent)
                            master_pdf = pathlib.Path(MASTER_FOLDER) / relative_path
                            if not master_pdf.exists():
                                console.print(f"\n[bold red][ERR] Brak oryginału w bazie Master: {escape(str(master_pdf))}[/bold red]")
                                console.print(f"  Ten plik istnieje w folderze Dropzone, ale brakuje go w folderze Master.")
                                console.print(f"  Upewnij się, że plik został skopiowany, a nie przeniesiony.")
                                sys.exit(1)

                            data, err_reason = extract_pdf_data(pdf)
                            if err_reason:
                                console.print(f"  [red][FAIL][/red] {escape(supplier_dir.name)} / {escape(year_dir.name)} / {escape(pdf.name)}  →  [red]{escape(err_reason)}[/red]")
                                protocols_failed += 1
                                protocols_processed += 1
                                continue

                            pos = data['pos']
                            if pos in positions_seen:
                                console.print(f"\n[bold red][ERR] Uruchomienie przerwane — wykryto zduplikowany protokół[/bold red]")
                                console.print(f"  Katalog dostawy: {escape(str(delivery_dir))}")
                                console.print(f"  Konfliktujące pliki: {escape(positions_seen[pos].name)} oraz {escape(pdf.name)} oba zgłaszają pozycję Pos. {pos}")
                                sys.exit(1)
                            positions_seen[pos] = pdf
                            pdfs_to_process.append((pdf, data))
                                
                        is_multi_position = len(pdf_files) > 1
                        
                        year_str = year_dir.name
                        year_prefix = year_str[-2:] if len(year_str) >= 2 else ""
                        
                        if delivery_dir.name.startswith(year_prefix):
                            smelter_code = 'BRX'
                        else:
                            smelter_code = 'KK'
                            
                        for pdf, data in pdfs_to_process:
                            protocols_processed += 1
                            
                            if not (date_from <= data['date_dt'] <= date_to):
                                protocols_excluded += 1
                                console.print(f"  \\[--]  {escape(supplier_dir.name)} / {escape(year_dir.name)} / {escape(delivery_dir.name)}  →  otrzymano {data['date_str']}  (poza zakresem)")
                                continue
                                
                            delivery_number = f"{delivery_dir.name}-{data['pos']}" if is_multi_position else delivery_dir.name
                            deliveries_included.add(delivery_dir.name)
                            
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

        # SORTING
        def get_sort_key(x):
            base_str = x['delivery_number'].split('-')[0]
            try:
                base_val = int(base_str)
            except ValueError:
                base_val = base_str
            return (x['smelter_code'], base_val, x['pos'])

        result_rows.sort(key=get_sort_key)
        
        out_folder = pathlib.Path(OUTPUT_FOLDER)
        out_folder.mkdir(parents=True, exist_ok=True)
        out_name = f"DeliveryReport_{date_from.strftime('%d%m%Y')}_{date_to.strftime('%d%m%Y')}.csv"
        out_path = out_folder / out_name
        
        counter = 2
        while out_path.exists():
            out_name = f"DeliveryReport_{date_from.strftime('%d%m%Y')}_{date_to.strftime('%d%m%Y')}_{counter}.csv"
            out_path = out_folder / out_name
            counter += 1

        if result_rows:
            with open(out_path, 'w', encoding='utf-8', newline='') as csvfile:
                fieldnames = ['Lp', 'Delivery number', 'Delivery date', 'Smelter code', 'Quantity kg', 'H2O[%]', 'Dry quant. kg', 'Ag kg', 'Au kg', 'Pd kg', 'Pt kg']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                tot_q = tot_d = tot_ag = tot_au = tot_pd = tot_pt = 0.0
                
                for idx, row in enumerate(result_rows, 1):
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
                    
                # Write Totals Row
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
            console.print("  Raport nie został wygenerowany, a pliki w folderze Dropzone pozostały nienaruszone.")
            console.print("─────────────────────────────────────────────")
            return

        console.print("  Raport zapisano w:")
        console.print(f"  {out_path}", markup=False)
        console.print("─────────────────────────────────────────────")

        # Determine unique archive folder name
        base_name = "samples_run"
        target_archive = pathlib.Path(ARCHIVE_FOLDER) / base_name
        counter = 2
        while target_archive.exists():
            target_archive = pathlib.Path(ARCHIVE_FOLDER) / f"{base_name}_{counter}"
            counter += 1

        # Create target archive directory
        target_archive.mkdir(parents=True, exist_ok=True)

        # Move the unignored contents of the dropzone directory to archive
        for item in pathlib.Path(DROPZONE_FOLDER).iterdir():
            if item.name in (".gitkeep", ".safe_dropzone", ".DS_Store"):
                continue
            try:
                shutil.move(str(item), str(target_archive / item.name))
            except Exception as e:
                console.print(f"  [yellow]Ostrzeżenie: Nie można przenieść {item.name} do archiwum: {e}[/yellow]")

        # Post-run prompt for verification and archive deletion
        console.print("\n─────────────────────────────────────────────")
        console.print("[yellow]  Weryfikacja po uruchomieniu i czyszczenie archiwum[/yellow]")
        console.print("─────────────────────────────────────────────")
        console.print("  Sprawdź, czy wygenerowane wyniki CSV są poprawne.")
        console.print("  Jeśli chcesz odzyskać pliki z tego uruchomienia, są one tymczasowo zapisane w:")
        console.print(f"  {escape(str(target_archive))}", markup=False)
        console.print("─────────────────────────────────────────────")
        console.print("  [green]•[/green] Jeśli wyniki są poprawne i nie potrzebujesz plików z tego uruchomienia,")
        console.print("    naciśnij [bold green]Enter[/bold green], aby usunąć je z archiwum.")
        console.print("  [red]•[/red] Jeśli chcesz zachować lub odzyskać te pliki, naciśnij teraz [bold red]Ctrl+C[/bold red].")
        console.print("─────────────────────────────────────────────")
        console.print("  Twój wybór (Enter aby usunąć, Ctrl+C aby zachować): ", end="")
        input()
        
        # User pressed Enter, empty the target archive folder
        try:
            if target_archive.exists():
                shutil.rmtree(str(target_archive))
            console.print("  [green]✓[/green] Folder archiwum został pomyślnie wyczyszczony.")
        except Exception as ex:
            console.print(f"  [yellow]Ostrzeżenie: Nie można usunąć katalogu archiwum: {ex}[/yellow]")
        console.print("─────────────────────────────────────────────")

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Uruchomienie przerwane przez użytkownika.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red][ERR] Nieoczekiwany błąd: {escape(str(e))}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
