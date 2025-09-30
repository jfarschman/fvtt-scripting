import json
import os
import re
import time
import secrets # Foundry like a random id.

PLACEHOLDER_USER_ID = secrets.token_hex(8)

# --- TEMPLATES ---

def get_dh_action_template():
    """Returns a template for a Daggerheart item's nested action block."""
    return {
        "type": "action", "_id": None, "systemPath": "actions", "description": "",
        "chatDisplay": True, "actionType": "action", "cost": [], "uses": {},
        "damage": {"parts": []}, "target": {"type": "any"}, "effects": [],
        "roll": {"bonus": 0},
        "save": {"trait": None, "difficulty": None, "damageMod": "none"},
        "range": "close"
    }

def get_dh_feature_template():
    """Returns a fresh template for a Daggerheart feature."""
    return {
        "folder": None, "name": "New Feature", "type": "feature", "img": "icons/svg/mystery-man.svg",
        "system": { "description": "", "resource": None, "actions": {}, "originItemType": None, "multiclassOrigin": False },
        "effects": [], "flags": {},
        "_stats": { "coreVersion": "13.347", "systemId": "daggerheart", "systemVersion": "1.1.2", "createdTime": None, "modifiedTime": None, "lastModifiedBy": PLACEHOLDER_USER_ID }
    }

def get_dh_adversary_template():
    """Returns a fresh template for a Daggerheart adversary."""
    return {
        "name": "New Adversary", "type": "adversary", "img": "icons/svg/mystery-man.svg",
        "system": {
            "difficulty": 15, "damageThresholds": {"major": 12, "severe": 24},
            "resources": { "hitPoints": {"value": 0, "max": 6, "isReversed": True}, "stress": {"value": 0, "max": 5, "isReversed": True} },
            "resistance": { "physical": {"resistance": False, "immunity": False, "reduction": 0}, "magical": {"resistance": False, "immunity": False, "reduction": 0} },
            "type": "solo", "notes": "Converted from D&D 5e using Python script.", "tier": 2,
            "description": {"value": ""}, "motivesAndTactics": "Motives and tactics should be reviewed.",
        },
        "prototypeToken": {}, "items": [], "effects": [], "flags": {},
        "_stats": { "systemId": "daggerheart", "systemVersion": "1.1.2", "coreVersion": "13.347", "createdTime": None, "modifiedTime": None, "lastModifiedBy": PLACEHOLDER_USER_ID }
    }

# --- CONVERSION LOGIC ---

def convert_dnd_item_to_dh_feature(dnd_item):
    """Converts a single D&D 5e item object to a Daggerheart feature object."""
    print(f"  - Converting item: {dnd_item.get('name', 'Unknown Item')}")
    feature = get_dh_feature_template()
    
    feature['name'] = dnd_item.get('name', 'Unnamed Feature')
    feature['img'] = dnd_item.get('img', 'icons/svg/mystery-man.svg')
    
    description_html = ""
    description_source = dnd_item.get('system', {}).get('description')
    if isinstance(description_source, dict):
        description_html = description_source.get('value', '')
    elif isinstance(description_source, str):
        description_html = description_source
    
    if not description_html:
        print(f"    - WARNING: Could not find a description for '{feature['name']}'.")
        description_html = "<p>Description not found during conversion.</p>"
        
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

def map_cr_to_tier(cr):
    if cr < 1: return 1
    if cr <= 4: return 2
    if cr <= 10: return 3
    if cr <= 16: return 4
    return 5

def convert_dnd_actor_to_dh_adversary(dnd_actor, converted_features):
    """Converts a D&D 5e actor object to a Daggerheart adversary object."""
    print(f"\nConverting actor: {dnd_actor.get('name', 'Unknown Actor')}")
    adversary = get_dh_adversary_template()

    adversary['name'] = dnd_actor.get('name', 'Unnamed Adversary')
    adversary['img'] = dnd_actor.get('img', 'icons/svg/mystery-man.svg')
    adversary['prototypeToken'] = dnd_actor.get('prototypeToken', {})
    adversary['system']['description']['value'] = dnd_actor.get('system', {}).get('details', {}).get('biography', {}).get('value', '')

    # --- ⭐ BUG FIX: Robustly find the Armor Class value ---
    ac_object = dnd_actor.get('system', {}).get('attributes', {}).get('ac', {})
    ac = 10 # Default AC if not found

    if ac_object and isinstance(ac_object, dict):
        # Prefer 'value', fall back to 'flat', then finally to the default
        ac = ac_object.get('value', ac_object.get('flat', 10))

    # Final safety check to ensure ac is not None before using it
    if ac is None:
        ac = 10
        print(f"  - WARNING: Could not determine AC for this actor. Defaulting to {ac}.")
    
    adversary['system']['difficulty'] = max(10, ac)
    # --- End of Bug Fix ---
    
    print(f"  - Mapped AC {ac} to Difficulty {adversary['system']['difficulty']}")

    cr = dnd_actor.get('system', {}).get('details', {}).get('cr', 1)
    adversary['system']['tier'] = map_cr_to_tier(cr)
    print(f"  - Mapped CR {cr} to Tier {adversary['system']['tier']}")
    
    adversary['items'] = converted_features
    print(f"  - Embedded {len(converted_features)} features into the adversary file.")
    
    current_time_ms = int(time.time() * 1000)
    adversary['_stats']['createdTime'] = current_time_ms
    adversary['_stats']['modifiedTime'] = current_time_ms
    
    return adversary

def sanitize_filename(name):
    """Removes invalid characters from a string to make it a valid filename."""
    name = re.sub(r'[\(\)]', '', name)
    return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")

def process_dnd_export(filepath):
    """Main function to process a D&D 5e actor JSON export."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            dnd_actor_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at '{filepath}'")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'. Please ensure it's a valid JSON file.")
        return

    actor_folder_name = sanitize_filename(dnd_actor_data.get('name', 'Unnamed_Actor'))
    base_output_dir = "daggerheart_import_files"
    actor_output_dir = os.path.join(base_output_dir, actor_folder_name)
    os.makedirs(actor_output_dir, exist_ok=True)
    print(f"Output files will be saved in the '{actor_output_dir}' directory.")

    dnd_items = dnd_actor_data.get('items', [])
    converted_features_for_actor = []
    
    print("\n--- Converting Features ---")
    if not dnd_items:
        print("No items found in the actor file to convert.")
    
    for item in dnd_items:
        feature_data = convert_dnd_item_to_dh_feature(item)
        converted_features_for_actor.append(feature_data)
        
        feature_filename = f"feature_{sanitize_filename(feature_data['name'])}.json"
        feature_filepath = os.path.join(actor_output_dir, feature_filename)
        with open(feature_filepath, 'w', encoding='utf-8') as f:
            json.dump(feature_data, f, indent=4)
        print(f"    -> Saved to {feature_filepath}")

    adversary_data = convert_dnd_actor_to_dh_adversary(dnd_actor_data, converted_features_for_actor)
    
    adversary_filename = f"adversary_{sanitize_filename(adversary_data['name'])}.json"
    adversary_filepath = os.path.join(actor_output_dir, adversary_filename)
    with open(adversary_filepath, 'w', encoding='utf-8') as f:
        json.dump(adversary_data, f, indent=4)
    print(f"    -> Saved Adversary to {adversary_filepath}")
    
    print(f"\n✅ Conversion of '{filepath}' complete!")

# --- SCRIPT EXECUTION ---
if __name__ == "__main__":
    print("="*50)
    print("FoundryVTT D&D 5e to Daggerheart Batch Converter")
    print("="*50)
    
    current_directory = os.getcwd() 
    print(f"Scanning for .json files in: {current_directory}\n")
    
    found_files = 0
    # Loop through all files in the directory where the script is located
    for filename in os.listdir(current_directory):
        # Process only files that end with .json
        if filename.endswith('.json'):
            found_files += 1
            print(f"--- Processing file: {filename} ---")
            process_dnd_export(filename)
            print(f"--- Finished processing: {filename} ---\n")
            
    if found_files == 0:
        print("No .json files found. Please place your D&D 5e actor exports in the same directory as this script.")

    print("Batch conversion complete!")
