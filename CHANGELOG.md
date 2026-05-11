# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

### Changed

- Add custom `HelpFormatter` to render boolean flags in a compact `--[no-]flag` format instead of the default `--flag, --no-flag`.
- The following filtering category arguments have been renamed and converted to
boolean options, all defaulting to `True`:
  - `--show-packages` to `--[no-]packages`(default: --packages)
  - `--show-config` to `--[no-]kernel-config`(default: --kernel-config)
  - `--show-packageconfig` to `--[no-]packageconfig`(default: --packageconfig)
  - `--ignore-proprietary` to `--[no-]packages-proprietary`(default: --packages-proprietary)

### Fixed

### Removed

- Refocused the tool on producing complete and reliable spdx diff:
  - Removing output filtering options:
      - `--show-added`
      - `--show-changed`
      - `--show-removed`
  - The default behaviour is to show the full spdx diff, following arguments are removed:
      - `--full`
      - `--summary`

## [1.0.1] - 2026-02-12

### Added
- Initial stable release of spdx-diff
---

## Release Information

- **Version:** 1.0.1
- **Release Date:** 2026-02-12
- **Status:** Stable
- **Breaking Changes:** None (initial release)

This is the first stable release of spdx-diff.

---

<!-- Links -->
[unreleased]: https://github.com/bootlin/spdx-diff/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/bootlin/spdx-diff/releases/tag/v1.0.1
