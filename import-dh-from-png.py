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
            "type": "solo", "notes": "", "tier": 1, "description": "", "motivesAndTactics": "Not specified.",
            "attack": { "name": "Attack", "img": "icons/skills/melee/blood-slash-foam-red.webp", "_id": secrets.token_hex(8), "systemPath": "attack", "chatDisplay": False, "type": "attack", "range": "melee", "target": { "type": "any", "amount": 1 }, "roll": { "bonus": 0 }, "damage": { "parts": [ { "value": { "dice": "d6", "bonus": 0, "multiplier": "flat", "flatMultiplier": 1 }, "type": ["physical"] } ], "includeBase": False }, "actionType": "action" },
            "experiences": {}
        },
        "prototypeToken": {}, "items": [], "effects": [], "flags": {},
        "_stats": { "systemId": "daggerheart", "systemVersion": "1.1.2", "coreVersion": "13.347", "createdTime": None, "modifiedTime": None, "lastModifiedBy": PLACEHOLDER_USER_ID }
    }

# --- OCR and Parsing Logic ---
def correct_ocr_errors(text):
    """Corrects common OCR mistakes, especially with dice notation."""
    corrections = {'110': '1d10', '246': '2d6', '1410': '1d10'}
    for wrong, right in corrections.items():
        text = text.replace(wrong, right)
    return text

def parse_text_from_ocr(text):
    """Parses raw text from OCR, tailored for multiple stat block formats."""
    parsed_data = {}
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    parsed_data['name'] = lines[0] if lines else "Unnamed Adversary"
    tier_type_line = lines[1] if len(lines) > 1 else ""
    tier_match = re.search(r"Tier\s*(\d+)\s*(\w+)", tier_type_line, re.IGNORECASE)
    if tier_match:
        parsed_data['tier'] = int(tier_match.group(1))
        parsed_data['type'] = tier_match.group(2).lower()
    parsed_data['description'] = lines[2] if len(lines) > 2 else ""

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

    experience_match = re.search(r"Experience:\s*(.*?)\s*\+\s*(\d+)", text, re.IGNORECASE)
    if experience_match:
        parsed_data['experience'] = {"description": experience_match.group(1).strip(), "value": int(experience_match.group(2))}
    
    attack_match = re.search(r"ATK:\s*\+?(\d+)\s*[|¦]\s*([^:]+):\s*[^|¦]+\s*[|¦]\s*(.*)", text, re.IGNORECASE)
    if attack_match:
        damage_string = correct_ocr_errors(attack_match.group(3).strip())
        damage_dice_match = re.search(r'(\d+)d(\d+)(?:\s*\+\s*(\d+))?', damage_string)
        if damage_dice_match:
            parsed_data['attack'] = {
                "bonus": int(attack_match.group(1)), "name": attack_match.group(2).strip(),
                "num_dice": int(damage_dice_match.group(1)), "die_type": f"d{damage_dice_match.group(2)}",
                "damage_bonus": int(damage_dice_match.group(3)) if damage_dice_match.group(3) else 0
            }

    # ⭐ BUG FIX: Rebuilt the feature parsing logic to be more reliable.
    parsed_data['features'] = []
    try:
        features_text = re.split(r"FEATURES", text, flags=re.IGNORECASE)[-1].strip()
        feature_lines = features_text.split('\n')
        
        temp_features = []
        current_feature_lines = None
        title_pattern = re.compile(r"(.+?)\s*-\s*(Action|Passive|Reaction)$", re.IGNORECASE)

        for line in feature_lines:
            line = line.strip()
            if not line: continue
            
            match = title_pattern.match(line)
            if match:
                clean_name = match.group(1).strip()
                current_feature_lines = []
                temp_features.append({"name": clean_name, "desc_lines": current_feature_lines})
            elif current_feature_lines is not None:
                current_feature_lines.append(line)
                
        for feature in temp_features:
            if feature['desc_lines']:
                full_description = ' '.join(feature['desc_lines'])
                corrected_description = correct_ocr_errors(full_description)
                parsed_data['features'].append({"name": feature['name'], "description": f"<p>{corrected_description}</p>"})
    except IndexError:
        print("  - INFO: No primary 'FEATURES' section found.")
    return parsed_data

# --- JSON Generation Logic ---
def create_feature_json(feature_data):
    feature = get_dh_feature_template()
    feature['name'] = feature_data['name']
    description_html = feature_data['description']
    feature['system']['description'] = description_html
    action_id = secrets.token_hex(8)
    action_block = get_dh_action_template()
    action_block['_id'] = action_id
    action_block['description'] = description_html
    feature['system']['actions'][action_id] = action_block
    ts = int(time.time() * 1000)
    feature['_stats']['createdTime'] = ts
    feature['_stats']['modifiedTime'] = ts
    return feature

def create_adversary_json(parsed_data, converted_features):
    adversary = get_dh_adversary_template()
    adversary['name'] = parsed_data.get('name', 'Unnamed Adversary')
    adversary['system']['description'] = f"<p>{parsed_data.get('description', '')}</p>"
    adversary['system']['motivesAndTactics'] = parsed_data.get('motivesAndTactics', "Not specified.")
    
    if 'experience' in parsed_data:
        exp_id = secrets.token_hex(8)
        adversary['system']['experiences'][exp_id] = {
            "name": parsed_data['experience']['description'],
            "value": parsed_data['experience']['value'],
            "description": ""
        }
        adversary['system']['notes'] = ""
    
    if 'attack' in parsed_data:
        adversary['system']['attack']['name'] = parsed_data['attack']['name']
        adversary['system']['attack']['roll']['bonus'] = parsed_data['attack']['bonus']
        attack_damage = adversary['system']['attack']['damage']['parts'][0]['value']
        attack_damage['flatMultiplier'] = parsed_data['attack']['num_dice']
        attack_damage['dice'] = parsed_data['attack']['die_type']
        attack_damage['bonus'] = parsed_data['attack']['damage_bonus']

    adversary['system']['tier'] = parsed_data.get('tier', 1)
    adversary['system']['type'] = parsed_data.get('type', 'solo')
    adversary['system']['difficulty'] = parsed_data.get('difficulty', 10)
    adversary['system']['damageThresholds']['major'] = parsed_data.get('major_threshold', 1)
    adversary['system']['damageThresholds']['severe'] = parsed_data.get('severe_threshold', 2)
    adversary['system']['resources']['hitPoints']['max'] = parsed_data.get('hp', 1)
    adversary['system']['resources']['stress']['max'] = parsed_data.get('stress', 1)
    adversary['items'] = converted_features
    
    ts = int(time.time() * 1000)
    adversary['_stats']['createdTime'] = ts
    adversary['_stats']['modifiedTime'] = ts
    return adversary

# --- Main Processing Logic ---
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|,]', "", name).replace(" ", "_")

def process_png_export(filepath):
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
