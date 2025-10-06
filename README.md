# PCM Volume Adjuster for MSU-1

Adjust the volume of MSU-1 PCM audio files without breaking loop points.
Supports **linear factor** and **decibel (dB)** volume adjustment.
Tracks processed files with metadata to skip reprocessing.

---

## Features

* Adjust `.pcm` file volume while preserving loops.
* Batch processing via JSON configuration.
* Interactive JSON selection from `config/` folder, or provide a path directly.
* Skips files already processed with the same settings.
* Volume can be set as **linear factor** or **decibels (dB)**.
* Flexible metadata storage: global, per-config, or custom path.

---

## Usage

| Script               | Purpose                         | Input                                     | Output                | Metadata                   | Batch Processing |
| -------------------- | ------------------------------- | ----------------------------------------- | --------------------- | -------------------------- | ---------------- |
| `adjust_pcm_json.py` | Batch adjust PCM files via JSON | JSON config file or interactive selection | Adjusted `.pcm` files | Yes (`adjusted_meta.json`) | Yes              |
| `adjust_pcm.py`      | Single file quick adjust        | Input `.pcm`, factor or dB                | Adjusted `.pcm` file  | No                         | No               |

### Interactive Mode (`adjust_pcm_json.py`)

```bash
python adjust_pcm_json.py
```

* Lists JSON files in `config/` and lets you pick one (omits `example.json`).
* Enter `0` to exit without processing.
* If no config files exist, the program prompts the user to create one manually.

### Specify JSON File (`adjust_pcm_json.py`)

```bash
python adjust_pcm_json.py /path/to/config.json
```

* Uses the specified JSON configuration directly.

### Show Help

```bash
python adjust_pcm_json.py --help
```

---

## Configuration JSON

```jsonc
{
    "output_dir": "./adjusted",  // Folder where adjusted PCM files will be saved
    "metadata_mode": "global",   // Metadata storage mode:
                                 // "global"     → single metadata file for all JSON configs
                                 // "per_config" → separate metadata file per config, named after the JSON
                                 // "<custom_path>" → use a custom folder, metadata file will be named after the JSON
    "files": [
        {
            "path": "./tracks/intro.pcm",  // Path to the PCM file to adjust
            "factor": 0.8                  // Linear volume multiplier (1.0 = original volume)
        },
        {
            "path": "./tracks/battle_theme.pcm",
            "db": -3                       // Volume adjustment in decibels (overrides factor if specified)
        }
    ]
}
```

⚠️ **Note:** JSON standard does not support comments.
This example uses comments (`//`) for documentation only.
Remove them in your actual config files.


### Fields

* **output_dir**: Folder where adjusted `.pcm` files are saved.

* **metadata_mode** (optional): Where metadata is stored. Options:

  * `"global"` → single metadata file for all JSON configs, stored at `./metadata/global.adjusted_meta.json` (default).
  * `"per_config"` → separate metadata file for each JSON config, stored at `./metadata/<config_name>.adjusted_meta.json`.
  * **Custom path** → specify folder or full path.

    * If a folder is provided, the metadata file is created inside it, named after the JSON config.
    * If a full path is provided, the metadata is saved directly with that filename.

* **files**: List of PCM files to adjust.

  * `factor`: Linear multiplier (1.0 = original volume).
  * `db`: Volume in decibels (overrides `factor` if specified).

---

## Metadata Behavior (`adjust_pcm_json.py`)

* A metadata JSON file tracks which files were processed with which settings.
* Files unchanged with the same factor/dB are skipped.
* Changing the source file or settings triggers reprocessing.

---

## Single File Adjuster (`adjust_pcm.py`)

For quick volume adjustments of a single PCM file:

```bash
python adjust_pcm.py input.pcm output.pcm factor
```

* `factor`: Linear multiplier (1.0 = original volume).

Or adjust using decibels:

```bash
python adjust_pcm.py input.pcm output.pcm --db -3
```

* `--db <value>`: Volume in decibels (negative to lower, positive to raise).

This version does **not** track metadata or batch multiple files; it only adjusts the specified file.

---

## Notes

* Existing adjusted files are **overwritten only if changes are detected** (for `adjust_pcm_json.py`).
* Loop points are preserved.
* Works on any platform with Python 3.x.

---

## License

This project is licensed under the **MIT License** – see the [LICENSE](./LICENSE) file for details.
