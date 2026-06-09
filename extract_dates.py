"""
Temporary script to extract finalization dates from ALL Sampling protocol PDFs
and reorganize them into month folders.

New structure: company_name/year/month/delivery_number/files
"""
import re
import pathlib
import shutil
import pdfplumber

samples_root = pathlib.Path("samples/Dostawcy-kopia")

# Collect delivery folder -> earliest month mapping
delivery_info = {}  # key: delivery folder path, value: month string (01-12)

for pdf_path in sorted(samples_root.rglob("*.pdf")):
    name_lower = pdf_path.name.lower()
    if not (name_lower.startswith("sampling protocol") or name_lower.startswith("sampling_protocol")):
        continue
    
    delivery_folder = pdf_path.parent
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            
            # Try Date of receipt labels, fallback to first date in file
            receipt_date = None
            label_matches = re.findall(
                r"(?:Date of receipt|Eingangsdatum|D[aá]tum prijatia|D[aá]tum dodania|D[aá]tum doru[cč]enia)\s*:\s*(\d{2}\.\d{2}\.\d{4})", 
                text, re.IGNORECASE
            )
            if label_matches:
                receipt_date = label_matches[0]
            else:
                fallback_matches = re.findall(r"\b(\d{2}\.\d{2}\.\d{4})\b", text)
                if fallback_matches:
                    receipt_date = fallback_matches[0]

            if receipt_date:
                month = receipt_date.split(".")[1]
                
                # Use earliest month for the delivery folder
                if delivery_folder not in delivery_info:
                    delivery_info[delivery_folder] = month
                elif month < delivery_info[delivery_folder]:
                    delivery_info[delivery_folder] = month
    except Exception as e:
        print(f"ERROR reading {pdf_path}: {e}")

# Now reorganize: move each delivery folder into the correct month subfolder
for delivery_folder, month in sorted(delivery_info.items()):
    # Current: company/year/delivery_number
    # Target:  company/year/month/delivery_number
    year_folder = delivery_folder.parent
    company_folder = year_folder.parent
    delivery_name = delivery_folder.name
    year_name = year_folder.name
    
    target_month_folder = year_folder / month
    target_delivery_folder = target_month_folder / delivery_name
    
    # Skip if already in a month folder
    if year_folder.name in [f"{i:02d}" for i in range(1, 13)]:
        print(f"SKIP (already in month folder): {delivery_folder.relative_to(samples_root)}")
        continue
    
    print(f"MOVE: {delivery_folder.relative_to(samples_root)} -> {target_delivery_folder.relative_to(samples_root)}  (month={month})")
    target_month_folder.mkdir(parents=True, exist_ok=True)
    shutil.move(str(delivery_folder), str(target_delivery_folder))

print("\nDone! Reorganization complete.")
