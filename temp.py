import re

def clean_and_map_tags_from_file(file_path: str) -> list:
    raw_tags = []
    
    # 1. Read from the file line by line
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            cleaned_tag = line.strip().lower()
            if cleaned_tag:  # Ignore completely empty lines
                raw_tags.append(cleaned_tag)
    
    # 2. Deduplicate using a Set
    unique_tags = set(raw_tags)
    
    # 3. The "Subjectivity" Blocklist
    # These words almost always indicate a tag that OpenStreetMap CANNOT map.
    forbidden_keywords = [
        "atmosphere", "event", "welcome", 
        "neutral", "led space", "owned", "inclusive", "policy", 
        "zone", "vibe", "slam", "class", "tasting", "activities",
        "introvert", "extrovert", "solo", "traveler"
    ]
    
    clean_tags = []
    purged_tags = []
    
    for tag in unique_tags:
        # Check if any forbidden keyword exists in the tag
        is_subjective = any(forbidden_word in tag for forbidden_word in forbidden_keywords)
        
        # We also want to drop tags that are too long (likely full sentences/descriptions)
        is_too_long = len(tag.split()) > 4
        
        if is_subjective or is_too_long:
            purged_tags.append(tag)
        else:
            clean_tags.append(tag)
            
    # Sort alphabetically for easy reading
    clean_tags.sort()
    purged_tags.sort()
    
    print(f"Started with {len(raw_tags)} raw tags.")
    print(f"Removed {len(raw_tags) - len(unique_tags)} exact duplicates.")
    print(f"Purged {len(purged_tags)} unmappable 'vibe' tags.")
    print(f"Final App-Ready Tags: {len(clean_tags)}")
    print("-" * 30)
    print("PURGED TAGS (Examples):")
    print(purged_tags[:10]) # Print first 10 to verify it worked
    
    return clean_tags

# --- Specify your file name here ---
# Make sure the text file is in the same folder as this Python script
filename = "filters2.txt"

# Run the function
final_list = clean_and_map_tags_from_file(filename)

print("-" * 30)
print("CLEAN FINAL LIST:")

counter = 1
for tag in final_list:
    print(str(counter)+':'+tag, end=',')
    counter += 1