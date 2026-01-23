# Installation

## Method 1: Quick Install (System-wide)

```bash
cd sbom-diff
pip install . --break-system-packages
```

**Use for:** Quick testing, single-user systems

---

## Method 2: Virtual Environment (Recommended)

```bash
cd sbom-diff

# Create virtual environment
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Install
pip install -e .

# Use the tool
sbom-diff --help

# When done
deactivate
```

**Use for:** Development, multiple projects, safety

**Note:** The `-e` flag allows code changes to take effect immediately without reinstalling.

---

## Usage

After installation:

```bash
# Show help
sbom-diff --help

# Compare two SPDX files
sbom-diff reference.json new.json

# Show summary only
sbom-diff reference.json new.json --summary

# JSON output for automation
sbom-diff reference.json new.json --format json --output results.json
```

See `README.md` for full documentation.

---

## Uninstall

**System-wide:**
```bash
pip uninstall sbom-diff
```

**Virtual environment:**
```bash
source .venv/bin/activate
pip uninstall sbom-diff
deactivate
```

Or simply delete the `.venv/` directory.
