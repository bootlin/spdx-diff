# SBOM KernelDiff Tool

A lightweight Python CLI tool to compare **SPDX3 SBOMs** or **Linux kernel config files**, and detect differences in software packages or kernel configuration.

## Features

-  Compare two SPDX3 SBOM JSON files and detect:
    -  Added, removed, and changed software packages
-  Compare two Linux kernel `.config` files:
    -  Identify changes in kernel build options
-  Export diff results as YAML

# How to use

## Command-line usage

### Basic Syntax

```bash
$ sbom-diff-tool <reference_file> <new_file> --mode [spdx|kconfig] [options]
```

### Options

| Option        | Description                                                |
|---------------|------------------------------------------------------------|
| `--mode`      | Comparison mode: `spdx` or `kconfig` (required)            |
| `--full`      | Show full diff output, even if a section is empty          |
| `--output`    | Output YAML file path                                      |

## Example: SBOM Comparison

```bash
$ sbom-diff-tool old.spdx.json new.spdx.json --mode sbom --full
```

**Example Output:**

Example bumping package version
```
> ./sbom-diff-tool --mode spdx tests/test_spdx/new-package.spdx.json tests/test_spdx/new-package-version.spdx.json
[INFO] Opening SPDX file: tests/test_spdx/new-package.spdx.json
[INFO] Found 2361 elements in the SPDX3 document.
[INFO] Extracted 37 valid software packages.
[INFO] Opening SPDX file: tests/test_spdx/new-package-version.spdx.json
[INFO] Found 2361 elements in the SPDX3 document.
[INFO] Extracted 37 valid software packages.

Changed:
 ~ i2c-tools: 4.3 → 4.4
[INFO] Writing diff results to spdx_diff_20250620-164525.yaml
```

YAML output

```yaml
added: {}
removed: {}
changed:
  i2c-tools:
    from: '4.3'
    to: '4.4'
```

## Example: Kernel Config Comparison

```bash
$ sbom-diff-tool old.config new.config --mode kconfig --output kernel_diff.yaml
```

**Example Output:**

Example adding new kernel configuration (n -> y)

```
> ./sbom-diff-tool --mode kconfig tests/test_kerneldiff/reference_kconfig tests/test_kerneldiff/kconfig5
[INFO] Reading kernel config file: tests/test_kerneldiff/reference_kconfig
[INFO] Extracted 586 kernel config entries.
[INFO] Reading kernel config file: defconfig
[INFO] Extracted 587 kernel config entries.

Added:
 + CONFIG_PARPORT_1284: y
[INFO] Writing diff results to kconfig_diff_20250620-162533.yaml
```

YAML output
```yaml
added:
  CONFIG_PARPORT_1284: y
removed: {}
changed: {}
```

## Project Structure

```text
├── LICENSE
├── README.md
├── sbom-diff-tool
└── tests
    ├── test_kerneldiff # Tests related to kernel configuration comparisons
    │   ├── kconfig1    # Change a component from y to n
    │   ├── kconfig2    # Change a component from m to n
    │   ├── kconfig3    # Change a component from y to m
    │   ├── kconfig4    # Change a component from m to y
    │   ├── kconfig5    # Change a component from n to y
    │   ├── kconfig6    # Change a component from n to m
    │   └── reference_kconfig
    └── test_spdx             # Tests for SPDX SBOM comparison functionality
        ├── new-package.spdx.json
        ├── new-package-version.spdx.json
        └── reference-sbom.spdx.json
```

# Dependencies

* PyYAML: https://pypi.org/project/PyYAML/ for handling YAML.
