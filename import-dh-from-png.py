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
# Uncomment and update the line below if the script can't find Tesseract.
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

PLACEHOLDER_USER_ID = secrets.token_hex(8)

# --- JSON TEMPLATES (Unchanged from previous version) ---
def get_dh_action_template():
    return { "type": "action", "_id": None, "systemPath": "actions", "description": "", "chatDisplay": True, "actionType": "action", "cost": [], "uses": {}, "damage": {"parts": []}, "target": {"type": "any"}, "effects": [], "roll": {"bonus": 0}, "save": {"trait": None, "difficulty": None, "damageMod": "none"}, "range": "close" }

def get_dh_feature_template():
    return { "folder": None, "name": "New Feature", "type": "feature", "img": "icons/svg/mystery-man.svg", "system": { "description": "", "resource": None, "actions": {}, "originItemType": None, "multiclassOrigin": False }, "effects": [], "flags": {}, "_stats": { "coreVersion": "13.347", "systemId": "daggerheart", "systemVersion": "1.1.2", "createdTime": None, "modifiedTime": None, "lastModifiedBy": PLACEHOLDER_USER_ID } }

def get_dh_adversary_template():
    return { "name": "New Adversary", "type": "adversary", "img": "icons/svg/mystery-man.svg", "system": { "difficulty": 10, "damageThresholds": {"major": 1, "severe": 2}, "resources": { "hitPoints": {"value": 0, "max": 6, "isReversed": True}, "stress": {"value": 0, "max": 5, "isReversed": True} }, "resistance": { "physical": {"resistance": False, "immunity": False, "reduction": 0}, "magical": {"resistance": False, "immunity": False, "reduction": 0} }, "type": "solo", "notes": "Converted from PNG using Python script.", "tier": 1, "description": {"value": ""}, "motivesAndTactics": "Motives and tactics need to be reviewed.", }, "prototypeToken": {}, "items": [], "effects": [], "flags": {}, "_stats": { "systemId": "daggerheart", "systemVersion": "1.1.2", "coreVersion": "13.347", "createdTime": None, "modifiedTime": None, "lastModifiedBy": PLACEHOLDER_USER_ID } }

# --- NEW: OCR and Parsing Logic ---

def parse_text_from_ocr(text):
    """
    Parses raw text from OCR into a structured dictionary.
    This function uses regular expressions and might need tweaking
    based on the exact format of your stat blocks.
    """
    parsed_data = {}
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # Basic Info (assumed to be at the top)
    parsed_data['name'] = lines[0] if lines else "Unnamed Adversary"
    
    # Tier and Type (e.g., "Tier 2 Solo Adversary")
    tier_match = re.search(r"Tier\s*(\d+)\s*(\w+)", text, re.IGNORECASE)
    if tier_match:
        parsed_data['tier'] = int(tier_match.group(1))
        parsed_data['type'] = tier_match.group(2).lower()

    # Key-Value Stats
    difficulty_match = re.search(r"Difficulty[:\s]+(\d+)", text, re.IGNORECASE)
    if difficulty_match:
        parsed_data['difficulty'] = int(difficulty_match.group(1))

    thresholds_match = re.search(r"Major\s*(\d+)[,\s]+Severe\s*(\d+)", text, re.IGNORECASE)
    if thresholds_match:
        parsed_data['major_threshold'] = int(thresholds_match.group(1))
        parsed_data['severe_threshold'] = int(thresholds_match.group(2))

    # Features
    parsed_data['features'] = []
    try:
        # Find the text block that contains features (assuming it starts with "FEATURES" or similar)
        features_text = re.split(r"FEATURES|ACTIONS|REACTIONS", text, flags=re.IGNORECASE)[-1]
        
        # Split features by blank lines between them
        feature_blocks = re.split(r'\n\s*\n', features_text.strip())

        for block in feature_blocks:
            block_lines = block.strip().split('\n')
            if not block_lines:
                continue
            
            feature_name = block_lines[0].strip()
            # Clean up common OCR mistakes on names
            if feature_name.endswith('.') or feature_name.endswith(':'):
                feature_name = feature_name[:-1]

            feature_desc = ' '.join(block_lines[1:]).strip()
            
            # Simple validation to avoid adding empty/junk features
            if len(feature_name) > 2 and len(feature_desc) > 5:
                parsed_data['features'].append({"name": feature_name, "description": f"<p>{feature_desc}</p>"})
    except (IndexError, AttributeError):
        print("  - WARNING: Could not find or parse a features block.")

    return parsed_data


# --- JSON Generation Logic (Updated to use parsed data) ---

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
    adversary['system']['tier'] = parsed_data.get('tier', 1)
    adversary['system']['type'] = parsed_data.get('type', 'solo')
    adversary['system']['difficulty'] = parsed_data.get('difficulty', 10)
    adversary['system']['damageThresholds']['major'] = parsed_data.get('major_threshold', 1)
    adversary['system']['damageThresholds']['severe'] = parsed_data.get('severe_threshold', 2)
    adversary['items'] = converted_features
    
    current_time_ms = int(time.time() * 1000)
    adversary['_stats']['createdTime'] = current_time_ms
    adversary['_stats']['modifiedTime'] = current_time_ms
    return adversary

# --- Main Processing Logic ---

def sanitize_filename(name):
    """Removes invalid characters from a string to make it a valid filename."""
    name = re.sub(r'[\(\)]', '', name)
    return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")

def process_png_export(filepath):
    """Main function to process a single stat block PNG."""
    try:
        # Step 1: Perform OCR to get raw text from the image
        print("  - Reading text from image...")
        text = pytesseract.image_to_string(Image.open(filepath))
        
        # Step 2: Parse the raw text into structured data
        print("  - Parsing extracted text...")
        parsed_data = parse_text_from_ocr(text)
        
        if not parsed_data.get('name'):
             print(f"  - WARNING: Could not determine adversary name for {os.path.basename(filepath)}. Skipping.")
             return

        # Step 3: Create output directory structure
        actor_folder_name = sanitize_filename(parsed_data['name'])
        base_output_dir = "daggerheart_import_files"
        actor_output_dir = os.path.join(base_output_dir, actor_folder_name)
        os.makedirs(actor_output_dir, exist_ok=True)
        print(f"  - Saving files to '{actor_output_dir}'")
        
        # Step 4: Convert parsed features into JSON files
        converted_features = []
        for feature_data in parsed_data['features']:
            feature_json = create_feature_json(feature_data)
            converted_features.append(feature_json)
            
            feature_filename = f"feature_{sanitize_filename(feature_json['name'])}.json"
            feature_filepath = os.path.join(actor_output_dir, feature_filename)
            with open(feature_filepath, 'w', encoding='utf-8') as f:
                json.dump(feature_json, f, indent=4)
        
        # Step 5: Create and save the main adversary JSON
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
