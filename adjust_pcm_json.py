import struct
import sys
import os
import json
import math

DEFAULT_METADATA_MODE = "global"  # default metadata mode
METADATA_FOLDER = "./metadata"    # base folder for global/per_config metadata

def select_json_from_folder(config_dir):
    """Prompt the user to select a JSON file from the config folder, omitting example.json."""
    json_files = [f for f in os.listdir(config_dir)
                  if f.endswith(".json") and f != "example.json"]  # omit example.json
    if not json_files:
        print(f"No JSON files found in {config_dir} (other than example.json).")
        sys.exit(0)

    print("Select a JSON configuration file to use:")
    print("  0: Exit")
    for i, f in enumerate(json_files, start=1):
        print(f"  {i}: {f}")

    while True:
        choice = input("Enter the number of the file to use: ")
        if choice.isdigit():
            idx = int(choice)
            if idx == 0:
                print("Exiting program.")
                sys.exit(0)
            elif 1 <= idx <= len(json_files):
                return os.path.join(config_dir, json_files[idx-1])
        print("Invalid choice. Try again.")

def load_metadata(meta_path):
    """Load metadata from JSON if it exists, else return empty dict."""
    if os.path.isfile(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_metadata(meta_path, metadata):
    """Save metadata to JSON file, creating directories if needed."""
    os.makedirs(os.path.dirname(meta_path), exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)

def adjust_pcm_volume(infile, outfile, factor, db_value, metadata, meta_path):
    """Read PCM, adjust volume, write output, and update metadata."""
    src_mtime = os.path.getmtime(infile)
    meta_key = os.path.abspath(infile)
    prev_entry = metadata.get(meta_key)

    # Skip if already processed with same settings
    if prev_entry \
       and abs(prev_entry.get("factor") - factor) < 1e-6 \
       and abs(prev_entry.get("db") - db_value) < 1e-6 \
       and prev_entry.get("src_mtime") == src_mtime \
       and os.path.exists(outfile):
        print(f"  {os.path.basename(outfile)} is already up to date "
              f"(factor {factor:.3f}, {db_value:+.2f} dB), skipping.")
        return

    # Read PCM file
    with open(infile, "rb") as fin:
        header = fin.read(8)  # "MSU1" + loop offset
        pcm_data = fin.read()

    # Apply volume factor with clipping
    samples = struct.unpack("<" + "h" * (len(pcm_data) // 2), pcm_data)
    adjusted = [max(min(int(s * factor), 32767), -32768) for s in samples]
    new_pcm_data = struct.pack("<" + "h" * len(adjusted), *adjusted)

    # Write adjusted PCM
    with open(outfile, "wb") as fout:
        fout.write(header)
        fout.write(new_pcm_data)

    # Update metadata
    metadata[meta_key] = {
        "factor": factor,
        "db": db_value,
        "src_mtime": src_mtime
    }
    save_metadata(meta_path, metadata)

    print(f"  {os.path.basename(outfile)} → {outfile} "
          f"(factor {factor:.3f}, {db_value:+.2f} dB)")

if __name__ == "__main__":
    # Handle help argument
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("""
PCM Volume Adjuster for MSU-1 PCM files

Usage:
  python adjust_pcm_json.py [path/to/config.json]
    - Use a specific JSON configuration file anywhere.

  python adjust_pcm_json.py
    - Interactively choose a JSON file from ./config/
    - Enter 0 to exit.

JSON format:

{
    "output_dir": "./adjusted",
    "metadata_mode": "global",   # or "per_config" or full path
    "files": [
        {"path": "./tracks/intro.pcm", "factor": 0.8},
        {"path": "./tracks/battle_theme.pcm", "db": -3}
    ]
}

- `factor`: linear multiplier (1.0 = original volume)
- `db`: volume in decibels, automatically converted to multiplier
- `metadata_mode`:
    * "global": single shared metadata file at ./metadata/global.adjusted_meta.json
    * "per_config": separate metadata per JSON at ./metadata/<config_name>.adjusted_meta.json
    * custom path: folder or full path for metadata file, named after the JSON if folder
""")
        sys.exit(0)

    # Determine JSON config file
    if len(sys.argv) == 2:
        config_file = sys.argv[1]
        if not os.path.isfile(config_file):
            print(f"❌ Config file not found: {config_file}")
            sys.exit(1)
    else:
        config_dir = "./config"
        if not os.path.isdir(config_dir):
            print(f"No config folder found at {config_dir}. Please create it and add your JSON files.")
            sys.exit(1)
        config_file = select_json_from_folder(config_dir)

    # Load JSON configuration
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Output folder
    outdir = config.get("output_dir", "./adjusted")
    os.makedirs(outdir, exist_ok=True)

    # Determine metadata path
    metadata_mode = config.get("metadata_mode", DEFAULT_METADATA_MODE)

    if metadata_mode == "global":
        os.makedirs(METADATA_FOLDER, exist_ok=True)
        meta_path = os.path.join(METADATA_FOLDER, "global.adjusted_meta.json")
    elif metadata_mode == "per_config":
        os.makedirs(METADATA_FOLDER, exist_ok=True)
        base = os.path.splitext(os.path.basename(config_file))[0]
        meta_path = os.path.join(METADATA_FOLDER, f"{base}.adjusted_meta.json")
    else:
        # Custom path: can be folder or full path
        if os.path.isdir(metadata_mode) or metadata_mode.endswith(os.sep):
            os.makedirs(metadata_mode, exist_ok=True)
            base = os.path.splitext(os.path.basename(config_file))[0]
            meta_path = os.path.join(metadata_mode, f"{base}.adjusted_meta.json")
        else:
            # full path including filename
            os.makedirs(os.path.dirname(metadata_mode), exist_ok=True)
            meta_path = metadata_mode

    # Load existing metadata
    metadata = load_metadata(meta_path)

    files = config.get("files", [])
    if not files:
        print("⚠️ No files found in the JSON configuration.")
        sys.exit(0)

    print(f"Processing {len(files)} files...")
    for entry in files:
        infile = entry["path"]
        if "db" in entry:
            db_value = float(entry["db"])
            factor = 10 ** (db_value / 20)
        elif "factor" in entry:
            factor = float(entry["factor"])
            db_value = 20 * math.log10(factor) if factor > 0 else float("-inf")
        else:
            print(f"⚠️ No factor or db specified for {infile}, skipping.")
            continue

        name = os.path.basename(infile)
        outfile = os.path.join(outdir, name)

        if not os.path.isfile(infile):
            print(f"❌ File not found: {infile}")
            continue

        adjust_pcm_volume(infile, outfile, factor, db_value, metadata, meta_path)

    print("✅ All files have been processed.")
