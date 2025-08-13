import json
import os
import re
from pathlib import Path

# --- CONFIGURATION ---
INPUT_DIR = "input_5e"
OUTPUT_FILENAME = "conversion_sheet.txt"

def clean_html_for_text(raw_html):
    """
    Cleans HTML from a string for plain text output.
    Replaces list items with a dash and removes other tags.
    """
    if not raw_html:
        return ""
    # Replace list items with a dash and a newline for readability
    processed_text = raw_html.replace("</li>", "\n").replace("<li>", "- ")
    # Remove all other HTML tags
    processed_text = re.sub('<.*?>', '', processed_text)
    # Replace non-breaking spaces and strip leading/trailing whitespace
    return processed_text.replace(chr(160), ' ').strip()

# --- Main execution block ---
if __name__ == "__main__":
    # Create input directory if it doesn't exist
    Path(INPUT_DIR).mkdir(exist_ok=True)
    
    print(f"Starting data extraction from '{INPUT_DIR}/'")

    try:
        files_to_process = [f for f in os.listdir(INPUT_DIR) if f.endswith('.json')]
        if not files_to_process:
            print(f"Warning: No .json files found in the '{INPUT_DIR}' directory.")
    except FileNotFoundError:
        print(f"Error: Input directory '{INPUT_DIR}' not found. Please create it.")
        files_to_process = []

    # Open the single output file to write all content
    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as output_file:
        conversion_count = 0
        for filename in files_to_process:
            input_path = Path(INPUT_DIR) / filename
            
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    data_5e = json.load(f)

                # 1. Extract the specific fields you requested
                name = data_5e.get("name", "No Name Found")
                item_type = data_5e.get("type", "No Type Found")
                description_html = data_5e.get("system", {}).get("description", {}).get("value", "No Description Found")
                img_path = data_5e.get("img", "No Image Path Found")

                # 2. Remove HTML from the description
                cleaned_description = clean_html_for_text(description_html)

                # 3. Write the formatted block to the output file
                output_block = (
                    f"Name: {name}\n"
                    f"Type: {item_type}\n"
                    f"Image Path: {img_path}\n"
                    f"Description:\n{cleaned_description}\n"
                    f"----------------------------------------\n\n"
                )
                output_file.write(output_block)
                
                print(f"Processed '{filename}'")
                conversion_count += 1

            except Exception as e:
                print(f"Could not process '{filename}'. Error: {e}")

    print(f"\nExtraction complete. {conversion_count} items written to '{OUTPUT_FILENAME}'.")
