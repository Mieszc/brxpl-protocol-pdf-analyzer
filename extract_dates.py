"""
Temporary Utility: Reorganize Delivery Folders by Month

This script scans a raw directory structure of supplier folders, parses the date of receipt 
from each Sampling Protocol PDF inside, and reorganizes the folder structure by inserting a 
'Month' folder level.

Target layout transformation:
  From: {Supplier}/{Year}/{DeliveryNumber}/
  To:   {Supplier}/{Year}/{Month}/{DeliveryNumber}/

This was used to prep the original raw database before migrating to the 3-folder pipeline.
"""

import re
import pathlib
import shutil
import pdfplumber

# Root directory of the folders to reorganize
samples_root = pathlib.Path("samples/Dostawcy-kopia")

# Dictionary to hold the earliest derived month for each delivery directory.
# Key: delivery folder path (pathlib.Path)
# Value: month string (e.g., '01', '02', ..., '12')
delivery_info = {}

# Iterate recursively through all PDF files in the directory
for pdf_path in sorted(samples_root.rglob("*.pdf")):
    name_lower = pdf_path.name.lower()
    # Only process PDF files that are actually sampling protocols
    if not (name_lower.startswith("sampling protocol") or name_lower.startswith("sampling_protocol")):
        continue
    
    delivery_folder = pdf_path.parent
    
    try:
        # Extract text content from the PDF pages
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            
            # Find the date of receipt using multi-lingual labels:
            # - EN: Date of receipt
            # - DE: Eingangsdatum
            # - SK: Dátum prijatia, Dátum dodania, Dátum doručenia
            receipt_date = None
            label_matches = re.findall(
                r"(?:Date of receipt|Eingangsdatum|D[aá]tum prijatia|D[aá]tum dodania|D[aá]tum doru[cč]enia)\s*:\s*(\d{2}\.\d{2}\.\d{4})", 
                text, re.IGNORECASE
            )
            if label_matches:
                receipt_date = label_matches[0]
            else:
                # Fallback: Capture the first DD.MM.YYYY formatted date found in the document text
                fallback_matches = re.findall(r"\b(\d{2}\.\d{2}\.\d{4})\b", text)
                if fallback_matches:
                    receipt_date = fallback_matches[0]

            if receipt_date:
                # Derive month string from the DD.MM.YYYY formatted date
                month = receipt_date.split(".")[1]
                
                # If there are multiple positions/PDFs in the same delivery folder, 
                # we group them under the earliest month detected.
                if delivery_folder not in delivery_info:
                    delivery_info[delivery_folder] = month
                elif month < delivery_info[delivery_folder]:
                    delivery_info[delivery_folder] = month
    except Exception as e:
        print(f"ERROR reading {pdf_path}: {e}")

# Reorganize the folders: move each delivery folder into its corresponding month folder level
for delivery_folder, month in sorted(delivery_info.items()):
    # Current structure: SupplierName / Year / DeliveryNumber
    # Target structure:  SupplierName / Year / Month / DeliveryNumber
    year_folder = delivery_folder.parent
    company_folder = year_folder.parent
    delivery_name = delivery_folder.name
    year_name = year_folder.name
    
    target_month_folder = year_folder / month
    target_delivery_folder = target_month_folder / delivery_name
    
    # Safety Check: Skip if the folder is already correctly nested within a Month directory
    if year_folder.name in [f"{i:02d}" for i in range(1, 13)]:
        print(f"SKIP (already in month folder): {delivery_folder.relative_to(samples_root)}")
        continue
    
    print(f"MOVE: {delivery_folder.relative_to(samples_root)} -> {target_delivery_folder.relative_to(samples_root)}  (month={month})")
    target_month_folder.mkdir(parents=True, exist_ok=True)
    shutil.move(str(delivery_folder), str(target_delivery_folder))

print("\nDone! Reorganization complete.")

