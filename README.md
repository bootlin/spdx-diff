SPDX3 Diff Tool
===============

Overview
--------
This tool compares two SPDX3 JSON documents and reports differences in:

- Software packages (name + version)
- Kernel configuration parameters (CONFIG_*)
- PACKAGECONFIG entries

It produces both human-readable output (console) and a structured JSON diff file.

Usage
-----
    ./sbom-diff-tool reference.json new.json [OPTIONS]

Required arguments:
  reference              Path to the baseline SPDX3 JSON file.
  new                    Path to the newer SPDX3 JSON file.

Optional arguments:
  --full                 Show all entries (added, removed, changed), not only differences.
  --output <file>        Save diff results to the given JSON file.
                         Default: spdx_diff_<timestamp>.json
  --ignore-proprietary   Ignore packages with LicenseRef-Proprietary.

Output
------
The script prints differences grouped into three sections:

1. Packages
   - Added packages
   - Removed packages
   - Changed versions

2. Kernel Config (CONFIG_*)
   - Added keys
   - Removed keys
   - Modified values

3. PACKAGECONFIG
   - Features enabled in the new SPDX
   - Features removed compared to reference

Symbols:
  + added
  - removed
  ~ changed

JSON Diff File
--------------
The output file (default: spdx_diff_<timestamp>.json) contains a structured diff:
```
{
  "package_diff": {
    "added": { "pkgA": "1.2.3" },
    "removed": { "pkgB": "4.5.6" },
    "changed": { "pkgC": { "from": "1.0", "to": "2.0" } }
  },
  "kernel_config_diff": {
    "added": { "CONFIG_XYZ": "y" },
    "removed": { "CONFIG_ABC": "n" },
    "changed": { "CONFIG_DEF": { "from": "m", "to": "y" } }
  },
  "packageconfig_diff": {
    "added": ["feature1", "feature2"],
    "removed": ["feature3"]
  }
}
```

Logging
-------
The script uses Python’s logging module:
```
  INFO     Normal operations (file opened, counts, etc.)
  WARNING  Missing sections (no build_Build objects found)
  ERROR    Invalid input or format issues
```

Example
-------
    ./sbom-diff-tool base.json new.json --ignore-proprietary --full --output diff.json

Console output:
```
Packages - Added:
 + libfoo: 2.0

Packages - Changed:
 ~ zlib: 1.2.11 -> 1.2.13

Kernel Config - Removed:
 - CONFIG_OLD_FEATURE

PACKAGECONFIG - Added:
 + gtk
```
