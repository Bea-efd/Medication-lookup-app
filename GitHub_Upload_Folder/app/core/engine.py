import fitz  # PyMuPDF
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from database import get_db_session, SourceDocument

class KnowledgeBase:
    """Handles extracting text from various document formats."""
    
    @staticmethod
    def extract_text(file_path: str, source_type: str) -> str:
        """Extracts plain text from a supported file type."""
        text = ""
        try:
            if source_type == "pdf":
                doc = fitz.open(file_path)
                for page in doc:
                    text += page.get_text()
                doc.close()
            elif source_type in ["xlsx", "xls", "csv"]:
                # Convert tabular data row-by-row into structured text lines
                if source_type == "csv":
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                rows = []
                for _, row in df.iterrows():
                    row_parts = []
                    for col, val in row.items():
                        if pd.notna(val) and str(val).strip() and str(val).strip().lower() != 'nan':
                            row_parts.append(f"{col}: {val}")
                    rows.append(" | ".join(row_parts))
                text = "\n".join(rows)
            elif source_type == "txt":
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            elif source_type == "link":
                # Ensure file_path is treated as a URL here
                url = file_path
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Extract text, stripping HTML tags
                    text = soup.get_text(separator=' ', strip=True)
                except Exception as e:
                    print(f"Failed to fetch or parse URL {url}: {e}")
            # Note: docx would require python-docx.
            # Sticking to requested core logic for now.
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
        return text

    @staticmethod
    def get_active_corpus() -> Dict[str, Dict[str, str]]:
        """
        Retrieves all text from active sources in the database.
        Returns: Dict[source_id, {"name": source_name, "text": extracted_text}]
        """
        session = get_db_session()
        active_sources = session.query(SourceDocument).filter_by(is_active=True).all()
        
        corpus = {}
        for source in active_sources:
            if source.source_type == "link":
                target_path = source.url
            else:
                import os
                # Dynamically resolve path to ensure portability across different PCs
                app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                filename = os.path.basename(source.file_path)
                target_path = os.path.join(app_root, "storage", "documents", filename)
            
            if target_path:
                if source.source_type != "link" and not os.path.exists(target_path):
                    print(f"Warning: Storage document missing at {target_path}")
                    continue
                    
                text = KnowledgeBase.extract_text(target_path, source.source_type)
                if text:
                    corpus[source.id] = {"name": source.name, "text": text}
        session.close()
        return corpus

class LookupEngine:
    """The strict lookup engine for medications."""
    
    def __init__(self):
        self.corpus = KnowledgeBase.get_active_corpus()

    def search_medication(self, name: str, dose: str, allow_web: bool = True) -> Dict[str, Any]:
        """
        Searches the active corpus for the medication and dose.
        Strict rule: If not found, returns 'Not Found'.
        If allow_web is False, it will skip sources of type 'link'.
        """
        # Initialize default empty results with a list of matches
        result = {
            "medication": name,
            "dose": dose,
            "atc_codes": [],
            "matches": [],
            "sources": []
        }

        # Filter corpus if web is disabled
        session = get_db_session()
        active_sources = session.query(SourceDocument).filter_by(is_active=True).all()
        
        filtered_corpus = {}
        for source in active_sources:
            if not allow_web and source.source_type == "link":
                continue 
            
            # Check if this source is the BNF web link (by name or URL)
            is_bnf = ("bnf" in source.name.lower() or (source.url and "bnf.nice.org.uk" in source.url.lower()))
            if is_bnf and allow_web:
                # Perform dynamic lookup for this specific drug on BNF.
                
                # BNF Combination Drug Aliases
                bnf_aliases = {
                    "co-codamol": "codeine-with-paracetamol",
                    "co-dydramol": "dihydrocodeine-with-paracetamol",
                    "co-amoxiclav": "amoxicillin-with-clavulanic-acid",
                    "co-trimoxazole": "sulfamethoxazole-with-trimethoprim",
                    "co-beneldopa": "benserazide-with-levodopa",
                    "co-careldopa": "carbidopa-with-levodopa",
                    "co-codaprin": "aspirin-with-codeine",
                    "co-danthrusate": "dantron-with-docusate-sodium",
                    "co-magaldrox": "aluminium-hydroxide-with-magnesium-hydroxide"
                }
                
                name_lower = name.lower().strip()
                name_for_slug = bnf_aliases.get(name_lower, name_lower)
                
                # Gracefully drop words specifically to support long complex search terms (e.g. Ondansetron orodispersible tablets)
                slug_parts = name_for_slug.split()
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-GB,en;q=0.5'
                }
                
                responses = []
                for i in range(len(slug_parts), 0, -1):
                    drug_slug = '-'.join(slug_parts[:i])
                    url = f"https://bnf.nice.org.uk/drugs/{drug_slug}/medicinal-forms/"
                    try:
                        resp = requests.get(url, headers=headers, timeout=5)
                        resp.raise_for_status()
                        responses.append(resp)
                        break
                    except Exception:
                        url = f"https://bnf.nice.org.uk/drugs/{drug_slug}/"
                        try:
                            resp = requests.get(url, headers=headers, timeout=5)
                            resp.raise_for_status()
                            responses.append(resp)
                            break
                        except Exception:
                            pass
                
                # If exact match fails, check BNF A-Z index for all possible options
                if not responses and name.strip():
                    index_url = "https://bnf.nice.org.uk/drugs/"
                    try:
                        index_response = requests.get(index_url, headers=headers, timeout=5)
                        if index_response.status_code == 200:
                            from bs4 import BeautifulSoup
                            index_soup = BeautifulSoup(index_response.text, 'html.parser')
                            
                            possible_slugs = []
                            target_part = slug_parts[0].lower()
                            for a in index_soup.find_all('a', href=True):
                                href = a['href']
                                if '/drugs/' in href:
                                    parts = [p for p in href.split('/') if p]
                                    if len(parts) >= 2 and parts[0] == 'drugs':
                                        slug = parts[1]
                                        if target_part in slug and slug not in possible_slugs:
                                            possible_slugs.append(slug)
                            
                            for slug in possible_slugs:
                                forms_url = f"https://bnf.nice.org.uk/drugs/{slug}/medicinal-forms/"
                                try:
                                    resp = requests.get(forms_url, headers=headers, timeout=5)
                                    resp.raise_for_status()
                                    responses.append(resp)
                                except Exception:
                                    base_url = f"https://bnf.nice.org.uk/drugs/{slug}/"
                                    try:
                                        resp = requests.get(base_url, headers=headers, timeout=5)
                                        resp.raise_for_status()
                                        responses.append(resp)
                                    except Exception:
                                        pass
                    except Exception as e:
                        print(f"Failed to fetch BNF A-Z index: {e}")

                if not responses:
                    print(f"Failed to fetch live BNF page for any combination of {name}")
                        
                if responses:
                    from bs4 import BeautifulSoup
                    all_parsed_products = []
                    
                    for response in responses:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        lines = soup.get_text(separator='\n', strip=True).split('\n')
                        
                        clean_lines = []
                        skip = False
                        for l in lines:
                            line = l.strip()
                            if not line: continue
                            if line.lower() in ["show", "hide", "all products", "there can be variation in the licensing of different medicines containing the same drug."]: 
                                continue
                                
                            if line == "Cautionary and advisory labels":
                                skip = True
                                continue
                            if skip:
                                if line == "Active ingredients":
                                    skip = False
                                    clean_lines.append(line)
                                continue
                                
                            clean_lines.append(line)
                        
                        parsed_products = []
                        current_product = ""
                        labels = ["Size", "Unit", "NHS indicative price", "Drug tariff price", "Drug tariff", "Legal category", "Active ingredients"]
                        expecting_value = False
                        
                        valid_form_keywords = ["mg", "ml", "microgram", "gram", "capsule", "tablet", "solution", "cream", "ointment", "suppositor", "patch", "inhaler", "drop", "spray", "lotion", "liquid", "suspension", "injection", "vial", "ampoule", "pen", "cartridge"]
                        ignore_starts = ("size", "unit", "nhs ", "drug ", "legal ", "active ", "cautionary", "schedule", "cd", "(", ")", "prescription", "show", "hide", "all products", "there can be")
                        
                        for line in clean_lines:
                            if line in labels:
                                current_product += line + ": "
                                expecting_value = True
                            else:
                                if expecting_value:
                                    current_product += line + " | "
                                    expecting_value = False
                                else:
                                    line_lower = line.lower()
                                    is_title = (
                                        ":" not in line and 
                                        not line_lower.startswith(ignore_starts) and 
                                        (any(kw in line_lower for kw in valid_form_keywords) or name_for_slug.replace("-", " ") in line_lower or name.lower() in line_lower)
                                    )
                                    
                                    if is_title and current_product.strip():
                                        parsed_products.append(current_product)
                                        current_product = line + " | "
                                    else:
                                        current_product += line + " | "
                                        
                        if current_product.strip():
                            parsed_products.append(current_product)
                            
                        # Cleanup generic headers from the beginning of products
                        cleaned_products = []
                        
                        for prod in parsed_products:
                            parts = [p.strip() for p in prod.split('|') if p.strip()]
                            start_idx = 0
                            for idx, p in enumerate(parts):
                                p_lower = p.lower()
                                if any(kw in p_lower for kw in valid_form_keywords) or name.lower() in p_lower:
                                    start_idx = idx
                                    break
                                    
                            base_parts = []
                            pack_parts = []
                            current_pack = []
                            
                            for p in parts[start_idx:]:
                                p_lower = p.lower()
                                if p_lower.startswith("size:") and current_pack:
                                    pack_parts.append(current_pack)
                                    current_pack = [p]
                                elif p_lower.startswith(("size:", "unit:", "nhs indicative price:", "drug tariff price:", "drug tariff:", "legal category:")):
                                    current_pack.append(p)
                                else:
                                    if not pack_parts and not current_pack:
                                        base_parts.append(p)
                                    else:
                                        current_pack.append(p)
                                        
                            if current_pack:
                                pack_parts.append(current_pack)
                                
                            if not pack_parts:
                                cleaned_products.append(" | ".join(base_parts))
                            else:
                                for pack in pack_parts:
                                    cleaned_products.append(" | ".join(base_parts + pack))
                            
                        # Remove trailing separators
                        cleaned_products = [re.sub(r'\|\s*\|', '|', p).strip(" |") for p in cleaned_products]
                        all_parsed_products.extend(cleaned_products)

                    text = "\n".join(all_parsed_products)

                    # Add this dynamically fetched text instead of the static corpus copy
                    filtered_corpus[source.id] = {"name": f"{source.name} (Live Web Search)", "text": text}
                    continue
            
            if source.id in self.corpus:
                filtered_corpus[source.id] = self.corpus[source.id]
        
        session.close()

        # If no sources are active
        if not filtered_corpus:
            return result
        
        # Advanced regex and categorizing logic
        name_lower = name.lower()
        dose_lower = dose.lower()
        
        for source_id, data in filtered_corpus.items():
            text = data["text"]
            lines = text.split('\n')
            
            source_name_lower = data["name"].lower()
            is_atc = "atc" in source_name_lower
            is_nhs = "nhs" in source_name_lower
            is_bnf = "bnf" in source_name_lower
            
            for line in lines:
                line_lower = line.lower()
                
                # Flexible Keyword Check: Does this line mention all words in the input medication name?
                name_keywords = name_lower.split()
                if all(re.search(rf'\b{re.escape(kw)}\b', line_lower) for kw in name_keywords):
                    # Found a potential match for the drug
                    if data["name"] not in result["sources"]:
                        result["sources"].append(data["name"])
                        
                    # 1. ATC Code extraction (strictly from ATC source or if any source is ok, we'll extract it anyway, but user asked for "1st ATC code - give me all possible codes")
                    atc_match = re.search(r'\b[A-Z][0-9]{2}[A-Z]{2}[0-9]{2}\b', line, re.IGNORECASE)
                    if atc_match:
                        code = atc_match.group(0).upper()
                        if code not in result["atc_codes"]:
                            result["atc_codes"].append(code)
                            
                    # Formulation extraction MUST happen before dose check to safely gate dose validation solely to the drug name
                    form_val = None
                    if is_bnf:
                        # Use the full product title to "tell me exactly what they are"
                        form_val = line.split(" | ")[0].strip()
                    elif is_nhs:
                        # Use the full product title from the 'Drug' column
                        drug_match = re.search(r'(?:Drug|Medication|Product)[\s:]*([^\|]+)', line, re.IGNORECASE)
                        if drug_match:
                            form_val = drug_match.group(1).strip()
                        else:
                            # Fallback to first chunk if we can't find the explicit header
                            form_val = line.split(" | ")[0].strip()
                    else:
                        form_match = re.search(r'(?:Formulation|Form)[\s:]*([A-Za-z\-\s]+?)(?:\||$)', line, re.IGNORECASE)
                        if not form_match:
                            modifiers = r'(?:dispersible|gastro-resistant|prolonged-release|modified-release|effervescent|chewable|soluble|enteric-coated|film-coated|sugar-coated|sublingual|buccal|vaginal|rectal|oral|hard|soft)'
                            bases = r'(?:tablets?|capsules?|solution|suspension|cream|ointment|drops|injection|syrup|vials?|suppositories)'
                            form_match = re.search(rf'\b((?:{modifiers}\s+){{0,2}}{bases})\b', line, re.IGNORECASE)
                            
                        if form_match:
                            val = form_match.group(1).strip()
                            if val and val.lower() != 'nan':
                                form_val = val.capitalize()
                                
                    # For strict dose check: We evaluate ONLY against the formulation (product title) if it's BNF/NHS to prevent aggregated text bugs.
                    dose_matched = True
                    if dose_lower:
                        dose_variants = [
                            dose_lower.strip(),
                            dose_lower.replace(" ", ""),
                            re.sub(r'(\d)\s*([a-zA-Z])', r'\1 \2', dose_lower)
                        ]
                        
                        search_target = form_val.lower() if form_val and (is_bnf or is_nhs) else line_lower
                        # Use negative lookbehind/lookahead to prevent substrings matching across digits (e.g., '5mg' matching inside '3.75mg' or '150mg')
                        dose_matched = any(re.search(rf'(?<![\d\.]){re.escape(variant)}(?![\d\.])', search_target) for variant in dose_variants)

                    if dose_matched:
                        if is_bnf and " | " not in line:
                            continue # Skip generic BNF headings that have no attributes attached

                        # Price extraction
                        price_match = re.search(r'(?:Price|Cost)[\s:]*([\$£€]?\s*\d+(?:\.\d{1,2})?)', line, re.IGNORECASE)
                        if not price_match:
                            price_match = re.search(r'[\$£€]\s?\d+(?:\.\d{2})?', line)
                        
                        price_val = None
                        if price_match:
                            price_val = price_match.group(1).strip() if len(price_match.groups()) > 0 and price_match.group(1) else price_match.group(0).strip()
                                
                        # Packet Size extraction
                        size_match = re.search(r'(?:Quantity|Qty|Size|Pack)[\s:]*([0-9a-zA-Z\s]+?)(?:\||$)', line, re.IGNORECASE)
                        if not size_match and not is_bnf:
                            size_match = re.search(r'\b(\d+\s*(?:tablets|capsules|ml|mg|drops|pack[s]?|vial[s]?))\b', line, re.IGNORECASE)
                            
                        size_val = None
                        if size_match:
                            val = size_match.group(1).strip()
                            if val and val.lower() != 'nan':
                                size_val = val
                                
                        # Category extraction for NHS
                        cat_val = None
                        if is_nhs:
                            cat_match = re.search(r'(?:Category|Cat)[\s:]*([A-Z]\b|[A-Za-z]+)', line)
                            if cat_match:
                                val = cat_match.group(1).strip()
                                if val.lower() != 'nan':
                                    cat_val = val
                                    
                        # Active Ingredient extraction
                        active_val = None
                        if is_bnf:
                            active_match = re.search(r'Active ingredients?:\s*([^\|]+)', line, re.IGNORECASE)
                            if active_match:
                                active_val = active_match.group(1).strip()
                        elif is_nhs:
                            active_match = re.search(r'Drug short name:\s*([^\|]+)', line, re.IGNORECASE)
                            if active_match:
                                active_val = active_match.group(1).strip()
                        
                        # Save the match if it has at least some data
                        if price_val or form_val or size_val or cat_val:
                            # Strict check for BNF: must have a proper price or size to avoid generic garbage parsing
                            if is_bnf and not (price_val or size_val):
                                continue
                                
                            match = {
                                "source": data["name"],
                                "formulation": form_val or "Not Found",
                                "active_ingredient": active_val or "Not Found",
                                "price": price_val or "Not Found",
                                "packet_size": size_val or "Not Found",
                                "category": cat_val or "Not Found"
                            }
                            
                            # Avoid duplicates from redundant parses
                            if match not in result["matches"]:
                                result["matches"].append(match)
        
        # Format the ATC list
        if not result["atc_codes"]:
            result["atc_codes"] = "Not Found"
        else:
            result["atc_codes"] = ", ".join(result["atc_codes"])
            
        if not result["sources"]:
            result["sources"] = "No answer found in the provided sources."
        else:
            result["sources"] = ", ".join(result["sources"])
            
        return result
