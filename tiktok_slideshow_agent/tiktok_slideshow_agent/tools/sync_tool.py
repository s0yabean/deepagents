import os
import json
import glob
from langchain_core.tools import tool

@tool
def sync_image_library() -> str:
    """
    Scans the image_library directory for matching file assets vs images.json metadata.
    Updates images.json to:
    1. Add new images found on disk (with default tags).
    2. Remove entries for images no longer on disk.
    
    Returns:
        A summary string of what was updated (e.g. "Added 2 images, Removed 1").
    """
    library_path = "/Users/mindreader/Desktop/deepagents-quickstarts/tiktok_slideshow_agent/image_library" # Hardcoded for this env
    json_path = os.path.join(library_path, "images.json")
    
    # 1. Load existing JSON
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
    else:
        data = []
        
    # Create a map for quick lookup: filename -> entry object
    existing_map = {item.get('filename'): item for item in data}
    
    # 2. Scan for actual files (recursive) -> getting relative paths or just filenames?
    # The current system seems to assume uniqueness by filename.
    # We will look for .jpg, .jpeg, .png
    extensions = ['*.jpg', '*.jpeg', '*.png']
    found_files = []
    
    for ext in extensions:
        # Recursive glob
        found_files.extend(glob.glob(os.path.join(library_path, "**", ext), recursive=True))
        
    # Map absolute paths to something we store.
    # From previous context, existing json has "filename": "slide_1.jpeg". 
    # But files are in subfolders? "motivational/slide_1.jpeg"?
    # Let's check if the filename in json is just basename or relative path.
    # Trace showed: "/image_library/motivational/slide_1.jpeg" for file, json had "slide_1.jpeg".
    # Assuming strict basename matching might be risky if duplicates exist.
    # Best approach: Update JSON to store 'absolute_path' to be helpful, 
    # but strictly key off 'filename' (basename) for now to match legacy format,
    # OR start storing relative path as filename.
    
    # Let's stick to: key = basename. 
    
    files_on_disk = {} # basename -> absolute_path
    for fpath in found_files:
        basename = os.path.basename(fpath)
        files_on_disk[basename] = fpath
        
    added_count = 0
    removed_count = 0
    
    new_data = []
    
    # 3. Process Disk vs JSON
    
    # First, keep valid existing entries
    for item in data:
        fname = item.get('filename')
        if fname in files_on_disk:
            # Update the absolute path to be sure (helper for designer)
            item['absolute_path'] = files_on_disk[fname]
            new_data.append(item)
            # Remove from files_on_disk so we know it's handled
            del files_on_disk[fname]
        else:
            # File in JSON but not on disk -> Remove
            removed_count += 1
            
    # Second, add remaining new files
    for basename, abs_path in files_on_disk.items():
        # Infer category from parent folder name
        parent_dir = os.path.basename(os.path.dirname(abs_path))
        if parent_dir == "image_library":
            category = "uncategorized"
        else:
            category = parent_dir
            
        new_entry = {
            "id": f"{category}_{basename.replace('.', '_')}", # simple ID gen
            "filename": basename,
            "category": category,
            "tags": ["new", category],
            "description": "Auto-discovered image.",
            "text_placement": "center",
            "absolute_path": abs_path 
        }
        new_data.append(new_entry)
        added_count += 1
        
    # 4. Save
    with open(json_path, 'w') as f:
        json.dump(new_data, f, indent=4)
        
    return f"Sync Complete. Added: {added_count}, Removed: {removed_count}. Total images: {len(new_data)}."
