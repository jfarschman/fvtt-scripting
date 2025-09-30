import json
import os
import re
import time
import secrets
try:
    import pytesseract
    from PIL import Image
except ImportError:
    print("Error: Required libraries not found. Please run 'pip install pillow pytesseract'")
    exit()

# --- Configuration ---
# On Windows, you might need to tell the script where Tesseract is installed.
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

PLACEHOLDER_USER_ID = secrets.token_hex(8)

# --- JSON TEMPLATES ---
def get_dh_action_template():
    return { "type": "action", "_id": None, "systemPath": "actions", "description": "", "chatDisplay": True, "actionType": "action", "cost": [], "uses": {}, "damage": {"parts": []}, "target": {"type": "any"}, "effects": [], "roll": {"bonus": 0}, "save": {"trait": None, "difficulty": None, "damageMod": "none"}, "range": "close" }

def get_dh_feature_template():
    return { "folder": None, "name": "New Feature", "type": "feature", "img": "icons/svg/mystery-man.svg", "system": { "description": "", "resource": None, "actions": {}, "originItemType": None, "multiclassOrigin": False }, "effects": [], "flags": {}, "_stats": { "coreVersion": "13.347", "systemId": "daggerheart", "systemVersion": "1.1.2", "createdTime": None, "modifiedTime": None, "lastModifiedBy": PLACEHOLDER_USER_ID } }

def get_dh_adversary_template():
    return {
        "name": "New Adversary", "type": "adversary", "img": "icons/svg/mystery-man.svg",
        "system": {
            "difficulty": 10, "damageThresholds": {"major": 1, "severe": 2},
            "resources": { "hitPoints": {"value": 0, "max": 1, "isReversed": True}, "stress": {"value": 0, "max": 1, "isReversed": True} },
            "resistance": { "physical": {"resistance": False, "immunity": False, "reduction": 0}, "magical": {"resistance": False, "immunity": False, "reduction": 0} },
            "type": "solo", "notes": "", "tier": 1,
            "description": "", "motivesAndTactics": "Not specified.",
        },
        "prototypeToken": {}, "items": [], "effects": [], "flags": {},
        "_stats": { "systemId": "daggerheart", "systemVersion": "1.1.2", "coreVersion": "13.347", "createdTime": None, "modifiedTime": None, "lastModifiedBy": PLACEHOLDER_USER_ID }
    }

# --- OCR and Parsing Logic ---

def parse_text_from_ocr(text):
    """
    Parses raw text from OCR into a structured dictionary,
    now tailored to the provided stat block format.
    """
    parsed_data = {}
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # --- TOP-LEVEL INFO ---
    parsed_data['name'] = lines[0] if lines else "Unnamed Adversary"
    
    tier_type_line = lines[1] if len(lines) > 1 else ""
    tier_match = re.search(r"Tier\s*(\d+)\s*(\w+)", tier_type_line, re.IGNORECASE)
    if tier_match:
        parsed_data['tier'] = int(tier_match.group(1))
        parsed_data['type'] = tier_match.group(2).lower()

    # The main description is the line directly after the Tier/Type
    parsed_data['description'] = lines[2] if len(lines) > 2 else ""

    # --- KEY-VALUE PAIRS ---
    motives_match = re.search(r"Motives & Tactics:\s*(.*)", text, re.IGNORECASE)
    if motives_match:
        parsed_data['motivesAndTactics'] = motives_match.group(1).strip()

    difficulty_match = re.search(r"Difficulty[:\s]+(\d+)", text, re.IGNORECASE)
    if difficulty_match:
        parsed_data['difficulty'] = int(difficulty_match.group(1))

    thresholds_match = re.search(r"Thresholds:\s*(\d+)\s*/\s*(\d+)", text, re.IGNORECASE)
    if thresholds_match:
        parsed_data['major_threshold'] = int(thresholds_match.group(1))
        parsed_data['severe_threshold'] = int(thresholds_match.group(2))
    
    hp_match = re.search(r"HP:\s*(\d+)", text, re.IGNORECASE)
    if hp_match:
        parsed_data['hp'] = int(hp_match.group(1))
        
    stress_match = re.search(r"Stress:\s*(\d+)", text, re.IGNORECASE)
    if stress_match:
        parsed_data['stress'] = int(stress_match.group(1))

    experience_match = re.search(r"Experience:\s*(.*)", text, re.IGNORECASE)
    if experience_match:
        parsed_data['experience'] = experience_match.group(1).strip()

    # --- FEATURES ---
    parsed_data['features'] = []
    
    # Add the ATK line as a feature if it exists
    attack_match = re.search(r"ATK:\s*(.*)", text, re.IGNORECASE)
    if attack_match:
        full_attack_string = attack_match.group(1).strip()
        parsed_data['features'].append({"name": "Attack", "description": f"<p>{full_attack_string}</p>"})

    try:
        features_text = re.split(r"FEATURES", text, flags=re.IGNORECASE)[-1]
        feature_blocks = re.split(r'\n\s*\n', features_text.strip())

        for block in feature_blocks:
            if not block: continue
            
            # Split feature name from description at the first colon
            if ':' in block:
                name, description = block.split(':', 1)
                parsed_data['features'].append({
                    "name": name.strip(),
                    "description": f"<p>{description.strip()}</p>"
                })
    except (IndexError, AttributeError):
        print("  - INFO: No primary 'FEATURES' section found.")

    return parsed_data

# --- JSON Generation Logic ---

def create_feature_json(feature_data):
    """Creates a Daggerheart feature JSON from parsed data."""
    feature = get_dh_feature_template()
    feature['name'] = feature_data['name']
    
    description_html = feature_data['description']
    feature['system']['description'] = description_html

    action_id = secrets.token_hex(8)
    action_block = get_dh_action_template()
    action_block['_id'] = action_id
    action_block['description'] = description_html
    feature['system']['actions'][action_id] = action_block
    
    current_time_ms = int(time.time() * 1000)
    feature['_stats']['createdTime'] = current_time_ms
    feature['_stats']['modifiedTime'] = current_time_ms
    return feature

def create_adversary_json(parsed_data, converted_features):
    """Creates a Daggerheart adversary JSON from parsed data."""
    adversary = get_dh_adversary_template()
    adversary['name'] = parsed_data.get('name', 'Unnamed Adversary')
    adversary['system']['description'] = f"<p>{parsed_data.get('description', '')}</p>"
    adversary['system']['motivesAndTactics'] = parsed_data.get('motivesAndTactics', "Not specified.")
    adversary['system']['notes'] = f"Experience: {parsed_data.get('experience', 'N/A')}"
    
    adversary['system']['tier'] = parsed_data.get('tier', 1)
    adversary['system']['type'] = parsed_data.get('type', 'solo')
    adversary['system']['difficulty'] = parsed_data.get('difficulty', 10)
    adversary['system']['damageThresholds']['major'] = parsed_data.get('major_threshold', 1)
    adversary['system']['damageThresholds']['severe'] = parsed_data.get('severe_threshold', 2)
    adversary['system']['resources']['hitPoints']['max'] = parsed_data.get('hp', 1)
    adversary['system']['resources']['stress']['max'] = parsed_data.get('stress', 1)

    adversary['items'] = converted_features
    
    current_time_ms = int(time.time() * 1000)
    adversary['_stats']['createdTime'] = current_time_ms
    adversary['_stats']['modifiedTime'] = current_time_ms
    return adversary

# --- Main Processing Logic ---

def sanitize_filename(name):
    """Removes invalid characters from a string to make it a valid filename."""
    name = re.sub(r'[\\/*?:"<>|,]', "", name).replace(" ", "_")
    return name

def process_png_export(filepath):
    """Main function to process a single stat block PNG."""
    try:
        print("  - Reading text from image...")
        text = pytesseract.image_to_string(Image.open(filepath))
        
        print("  - Parsing extracted text...")
        parsed_data = parse_text_from_ocr(text)
        
        if not parsed_data.get('name') or parsed_data['name'] == "Unnamed Adversary":
             print(f"  - WARNING: Could not determine adversary name for {os.path.basename(filepath)}. Skipping.")
             return

        actor_folder_name = sanitize_filename(parsed_data['name'])
        base_output_dir = "daggerheart_import_files"
        actor_output_dir = os.path.join(base_output_dir, actor_folder_name)
        os.makedirs(actor_output_dir, exist_ok=True)
        print(f"  - Saving files to '{actor_output_dir}'")
        
        converted_features = []
        for feature_data in parsed_data.get('features', []):
            feature_json = create_feature_json(feature_data)
            converted_features.append(feature_json)
            
            feature_filename = f"feature_{sanitize_filename(feature_json['name'])}.json"
            feature_filepath = os.path.join(actor_output_dir, feature_filename)
            with open(feature_filepath, 'w', encoding='utf-8') as f:
                json.dump(feature_json, f, indent=4)
        
        adversary_json = create_adversary_json(parsed_data, converted_features)
        adversary_filename = f"adversary_{sanitize_filename(adversary_json['name'])}.json"
        adversary_filepath = os.path.join(actor_output_dir, adversary_filename)
        with open(adversary_filepath, 'w', encoding='utf-8') as f:
            json.dump(adversary_json, f, indent=4)
        
        print(f"\n✅ Conversion of '{filepath}' complete!")

    except FileNotFoundError:
        print(f"Error: Input file not found at '{filepath}'")
    except Exception as e:
        print(f"An unexpected error occurred while processing {filepath}: {e}")

# --- SCRIPT EXECUTION ---
if __name__ == "__main__":
    print("="*50)
    print("FoundryVTT Daggerheart PNG to JSON Batch Converter")
    print("="*50)
    
    input_directory = "input_pngs"
    if not os.path.isdir(input_directory):
        print(f"Error: Input directory '{input_directory}' not found.")
        print("Please create it and place your stat block .png files inside.")
        exit()
        
    print(f"Scanning for .png files in: {input_directory}\n")
    
    found_files = 0
    for filename in os.listdir(input_directory):
        if filename.lower().endswith('.png'):
            found_files += 1
            filepath = os.path.join(input_directory, filename)
            print(f"--- Processing file: {filename} ---")
            process_png_export(filepath)
            print(f"--- Finished processing: {filename} ---\n")
            
    if found_files == 0:
        print(f"No .png files found in the '{input_directory}' directory.")

    print("Batch conversion complete!")
