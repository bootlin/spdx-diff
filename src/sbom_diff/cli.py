#
# SPDX-License-Identifier: GPL-2.0

import json
import logging
import pathlib
import re
from argparse import ArgumentParser
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from . import __version__

_logger = logging.getLogger(__name__)


def normalize_package_name(name: str) -> str:
    """
    Normalize package names, especially for kernel and kernel-modules.

    Returns:
        The normalized package name

    Examples:
        "kernel-6.12.43-00469-g647daef97a89" -> "kernel"
        "kernel-module-8021q-6.12.43-00469-g647daef97a89" -> "kernel-module-8021q"

    """
    # Pattern to match kernel version suffixes
    # Matches: X.Y.Z followed by any combination of alphanumeric, dots, underscores,
    # hyphens
    # Examples:
    #   - 6.12.43-linux-00469-g647daef97a89 (git-based)
    #   - 6.6.111-yocto-standard (branch-based)
    #   - 6.1.38-rt13 (RT kernel)
    kernel_version_pattern = r"-(\d+\.\d+(?:\.\d+)?[a-zA-Z0-9._-]*)$"

    match = re.search(kernel_version_pattern, name)
    return name[: match.start()] if match else name


def extract_spdx_data(
    json_path: pathlib.Path, ignore_proprietary: bool = False
) -> tuple[dict[str, str], dict[str, Any], dict[str, dict[str, str]]]:
    """
    Extract SPDX information (packages, kernel CONFIG, and PACKAGECONFIG).

    Extract SPDX package data, kernel CONFIG options, and PACKAGECONFIG entries from
    the SPDX JSON file. Kernel packages are automatically normalized.

    Args:
        json_path: Path to the SPDX3 JSON file
        ignore_proprietary: Whether to skip proprietary packages

    Returns:
        tuple[dict, dict, dict]:
            - packages: mapping of package names to versions
            - config: mapping of CONFIG_* keys to their values
            - packageconfig: mapping of package names to their PACKAGECONFIG features

    """
    _logger.info("Opening SPDX file: %s", json_path)
    try:
        with json_path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise ValueError("Failed to read or parse %s", json_path) from e

    graph = data.get("@graph")
    if not isinstance(graph, list):
        raise TypeError("SPDX3 file format is not recognized.")

    _logger.debug("Found %d elements in the SPDX3 document.", len(graph))

    packages: dict[str, str] = {}
    config: dict[str, Any] = {}
    packageconfig: dict[str, dict[str, str]] = defaultdict(dict)
    build_count = 0

    for item in graph:
        # Extract packages
        if item.get("type") == "software_Package":
            name: str | None = item.get("name")
            version: str | None = item.get("software_packageVersion")
            if not name or not version:
                continue

            license_expr: str | None = item.get("simplelicensing_licenseExpression")
            if ignore_proprietary and license_expr == "LicenseRef-Proprietary":
                _logger.info("Ignoring proprietary package: %s", name)
                continue

            sw_primary_purpose: str | None = item.get("software_primaryPurpose")
            if sw_primary_purpose != "install":
                continue

            # Always normalize kernel package names
            if name.startswith("kernel-") or name == "kernel":
                normalized_name = normalize_package_name(name)
                packages[normalized_name] = version
            else:
                packages[name] = version

        # Extract kernel config and PACKAGECONFIG
        if item.get("type") == "build_Build":
            build_count += 1

            build_name = item.get("name", "")
            pkg_name: str | None = None
            if ":" in build_name:
                pkg_name, _ = build_name.split(":", maxsplit=1)

            for param in item.get("build_parameter", []):
                if not isinstance(param, dict):
                    continue
                key = param.get("key")
                value = param.get("value")
                if not key or value is None:
                    continue

                if key.startswith("CONFIG_"):
                    config[key] = value
                elif key.startswith("PACKAGECONFIG:") and pkg_name:
                    _, feature = key.split(":", maxsplit=1)
                    packageconfig[pkg_name][feature] = value

    if build_count == 0:
        _logger.warning("No build_Build objects found.")

    _logger.debug(
        "Extracted %d packages, %d CONFIG_*, "
        "and %d packages with PACKAGECONFIG entries.",
        len(packages),
        len(config),
        len(packageconfig),
    )
    return packages, config, packageconfig


def compare_dicts(
    ref: dict[str, Any], new: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """
    Compare two dictionaries and return added, removed, and changed items.

    Args:
        ref: Reference dictionary
        new: New dictionary to compare

    Returns:
        tuple[dict, dict, dict]: added, removed, changed items

    """
    added = {k: v for k, v in new.items() if k not in ref}
    removed = {k: v for k, v in ref.items() if k not in new}
    changed = {
        k: {"from": ref[k], "to": new[k]} for k in ref if k in new and ref[k] != new[k]
    }
    return added, removed, changed


def compare_packageconfig(
    ref_pcfg: dict[str, dict[str, str]], new_pcfg: dict[str, dict[str, str]]
) -> tuple[
    dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, Any]]
]:
    """
    Compare PACKAGECONFIG dictionaries.

    Args:
        ref_pcfg: Reference PACKAGECONFIG mapping
        new_pcfg: New PACKAGECONFIG mapping

    Returns:
        tuple: added packages, removed packages, changed features per package

    """
    added_pkgs = {k: v for k, v in new_pcfg.items() if k not in ref_pcfg}
    removed_pkgs = {k: v for k, v in ref_pcfg.items() if k not in new_pcfg}

    changed_pkgs = {}
    for pkg, ref_features in ref_pcfg.items():
        new_features = new_pcfg.get(pkg)
        if new_features is None:
            continue

        added_features = {
            k: v for k, v in new_features.items() if k not in ref_features
        }
        removed_features = {
            k: v for k, v in ref_features.items() if k not in new_features
        }
        changed_features = {
            k: {"from": ref_features[k], "to": new_features[k]}
            for k in ref_features
            if k in new_features and ref_features[k] != new_features[k]
        }

        if added_features or removed_features or changed_features:
            changed_pkgs[pkg] = {
                "added": added_features,
                "removed": removed_features,
                "changed": changed_features,
            }

    return added_pkgs, removed_pkgs, changed_pkgs


def print_diff(
    title: str,
    added: Any,
    removed: Any,
    changed: Any = None,
    show_all: bool = False,
    show_added: bool = True,
    show_removed: bool = True,
    show_changed: bool = True,
) -> None:
    """
    Print differences between items.

    Args:
        title: Section title
        added: Added items
        removed: Removed items
        changed: Changed items
        show_all: Whether to show even if empty
        show_added: Whether to show added items
        show_removed: Whether to show removed items
        show_changed: Whether to show changed items

    """
    if show_added and (show_all or added):
        print(f"\n{title} - Added:")
        for k in sorted(added) if isinstance(added, dict) else added:
            print(f" + {k}" if isinstance(added, list) else f" + {k}: {added[k]}")

    if show_removed and (show_all or removed):
        print(f"\n{title} - Removed:")
        for k in sorted(removed) if isinstance(removed, dict) else removed:
            print(f" - {k}" if isinstance(removed, list) else f" - {k}: {removed[k]}")

    if show_changed and changed and (show_all or changed):
        print(f"\n{title} - Changed:")
        for k in sorted(changed):
            print(f" ~ {k}: {changed[k]['from']} -> {changed[k]['to']}")


def print_packageconfig_diff(
    added: dict[str, dict[str, str]],
    removed: dict[str, dict[str, str]],
    changed: dict[str, dict[str, Any]],
    show_all: bool = False,
    show_added: bool = True,
    show_removed: bool = True,
    show_changed: bool = True,
) -> None:
    """
    Print PACKAGECONFIG differences.

    Args:
        added: Added packages with their features
        removed: Removed packages with their features
        changed: Changed packages with feature differences
        show_all: Whether to show even if empty
        show_added: Whether to show added items
        show_removed: Whether to show removed items
        show_changed: Whether to show changed items

    """
    if show_added and (show_all or added):
        print("\nPACKAGECONFIG - Added Packages:")
        for pkg in sorted(added):
            print(f" + {pkg}:")
            for feature, value in sorted(added[pkg].items()):
                print(f"     {feature}: {value}")

    if show_removed and (show_all or removed):
        print("\nPACKAGECONFIG - Removed Packages:")
        for pkg in sorted(removed):
            print(f" - {pkg}:")
            for feature, value in sorted(removed[pkg].items()):
                print(f"     {feature}: {value}")

    if show_changed and (show_all or changed):
        print("\nPACKAGECONFIG - Changed Packages:")
        for pkg in sorted(changed):
            print(f" ~ {pkg}:")
            pkg_changes = changed[pkg]
            if pkg_changes.get("added"):
                for feature, value in sorted(pkg_changes["added"].items()):
                    print(f"     + {feature}: {value}")
            if pkg_changes.get("removed"):
                for feature, value in sorted(pkg_changes["removed"].items()):
                    print(f"     - {feature}: {value}")
            if pkg_changes.get("changed"):
                for feature, change in sorted(pkg_changes["changed"].items()):
                    print(f"     ~ {feature}: {change['from']} -> {change['to']}")


def print_summary(
    pkg_diff: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    cfg_diff: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    pcfg_diff: tuple[
        dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, Any]]
    ],
) -> None:
    """
    Print summary statistics of differences.

    Args:
        pkg_diff: Package differences
        cfg_diff: Kernel config differences
        pcfg_diff: PACKAGECONFIG differences

    """
    print("\nSPDX-SBOM-Diff Summary:\n")

    print("Packages:")
    print(f"  Added:   {len(pkg_diff[0])}")
    print(f"  Removed: {len(pkg_diff[1])}")
    print(f"  Changed: {len(pkg_diff[2])}")

    print("\nKernel Config:")
    print(f"  Added:   {len(cfg_diff[0])}")
    print(f"  Removed: {len(cfg_diff[1])}")
    print(f"  Changed: {len(cfg_diff[2])}")

    print("\nPACKAGECONFIG:")
    print(f"  Packages Added:   {len(pcfg_diff[0])}")
    print(f"  Packages Removed: {len(pcfg_diff[1])}")
    print(f"  Packages Changed: {len(pcfg_diff[2])}")

    # Count total feature changes
    total_features_added = sum(len(v.get("added", {})) for v in pcfg_diff[2].values())
    total_features_removed = sum(
        len(v.get("removed", {})) for v in pcfg_diff[2].values()
    )
    total_features_changed = sum(
        len(v.get("changed", {})) for v in pcfg_diff[2].values()
    )

    if total_features_added or total_features_removed or total_features_changed:
        print(f"  Features Added:   {total_features_added}")
        print(f"  Features Removed: {total_features_removed}")
        print(f"  Features Changed: {total_features_changed}")

    print()


def write_diff_to_json(
    pkg_diff: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    cfg_diff: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    pcfg_diff: tuple[
        dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, Any]]
    ],
    output_file: pathlib.Path,
) -> None:
    """
    Write diff results to a JSON file.

    Args:
        pkg_diff: Differences for packages
        cfg_diff: Differences for kernel config
        pcfg_diff: Differences for PACKAGECONFIG
        output_file: File path to write JSON

    """
    _logger.info("Writing diff results to %s", output_file)
    delta = {
        "package_diff": {
            "added": dict(sorted(pkg_diff[0].items())),
            "removed": dict(sorted(pkg_diff[1].items())),
            "changed": dict(sorted(pkg_diff[2].items())),
        },
        "kernel_config_diff": {
            "added": dict(sorted(cfg_diff[0].items())),
            "removed": dict(sorted(cfg_diff[1].items())),
            "changed": dict(sorted(cfg_diff[2].items())),
        },
        "packageconfig_diff": {
            "added": dict(sorted(pcfg_diff[0].items())),
            "removed": dict(sorted(pcfg_diff[1].items())),
            "changed": dict(sorted(pcfg_diff[2].items())),
        },
    }
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(delta, f, indent=2, ensure_ascii=False)


def main() -> None:
    """
    Main entry point.

    Parse arguments, extract SPDX data, compare, and print/write diffs.
    """
    parser = ArgumentParser(description="Compare SPDX3 JSON files")
    parser.add_argument(
        "--version", action="version", version=f"sbom-diff {__version__}"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v for INFO, -vv for DEBUG)",
    )
    parser.add_argument(
        "reference",
        metavar="PATH",
        type=pathlib.Path,
        help="Reference SPDX3 JSON file",
    )
    parser.add_argument(
        "new",
        metavar="PATH",
        type=pathlib.Path,
        help="New SPDX3 JSON file",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Show full diff output (added, removed, changed)",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="PATH",
        type=pathlib.Path,
        help="Optional output file name (JSON)",
    )
    parser.add_argument(
        "--ignore-proprietary",
        action="store_true",
        help="Ignore packages with LicenseRef-Proprietary",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show only summary statistics without detailed differences",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "both"],
        default="both",
        help="Output format: text (console only), json (file only), or both (default)",
    )

    # Output filtering options
    parser.add_argument(
        "--show-added",
        action="store_true",
        help="Show only added items",
    )
    parser.add_argument(
        "--show-removed",
        action="store_true",
        help="Show only removed items",
    )
    parser.add_argument(
        "--show-changed",
        action="store_true",
        help="Show only changed items",
    )
    parser.add_argument(
        "--show-packages",
        action="store_true",
        help="Show only package differences",
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Show only kernel config differences",
    )
    parser.add_argument(
        "--show-packageconfig",
        action="store_true",
        help="Show only PACKAGECONFIG differences",
    )

    args = parser.parse_args()

    log_level = logging.WARNING
    if args.verbose >= 2:
        log_level = logging.DEBUG
    elif args.verbose == 1:
        log_level = logging.INFO

    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s")

    timestamp = datetime.now(tz=timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")
    if args.output is None:
        args.output = pathlib.Path(f"spdx_diff_{timestamp}.json")

    # Determine what to show based on flags
    # If no specific show flags are set, show everything
    show_added = args.show_added or not (
        args.show_added or args.show_removed or args.show_changed
    )
    show_removed = args.show_removed or not (
        args.show_added or args.show_removed or args.show_changed
    )
    show_changed = args.show_changed or not (
        args.show_added or args.show_removed or args.show_changed
    )

    show_packages = args.show_packages or not (
        args.show_packages or args.show_config or args.show_packageconfig
    )
    show_config = args.show_config or not (
        args.show_packages or args.show_config or args.show_packageconfig
    )
    show_packageconfig = args.show_packageconfig or not (
        args.show_packages or args.show_config or args.show_packageconfig
    )

    try:
        ref_pkgs, ref_cfg, ref_pcfg = extract_spdx_data(
            args.reference, ignore_proprietary=args.ignore_proprietary
        )
        new_pkgs, new_cfg, new_pcfg = extract_spdx_data(
            args.new, ignore_proprietary=args.ignore_proprietary
        )
    except (ValueError, TypeError) as e:
        parser.error(str(e))

    pkg_diff = compare_dicts(ref_pkgs, new_pkgs)
    cfg_diff = compare_dicts(ref_cfg, new_cfg)
    pcfg_diff = compare_packageconfig(ref_pcfg, new_pcfg)

    # Print summary or full output
    if args.summary:
        print_summary(pkg_diff, cfg_diff, pcfg_diff)
    elif args.format in {"text", "both"}:
        if show_packages:
            print_diff(
                "Packages",
                *pkg_diff,
                show_all=args.full,
                show_added=show_added,
                show_removed=show_removed,
                show_changed=show_changed,
            )
        if show_config:
            print_diff(
                "Kernel Config",
                *cfg_diff,
                show_all=args.full,
                show_added=show_added,
                show_removed=show_removed,
                show_changed=show_changed,
            )
        if show_packageconfig:
            print_packageconfig_diff(
                *pcfg_diff,
                show_all=args.full,
                show_added=show_added,
                show_removed=show_removed,
                show_changed=show_changed,
            )

    if args.format in ["json", "both"]:
        write_diff_to_json(pkg_diff, cfg_diff, pcfg_diff, args.output)


if __name__ == "__main__":
    main()
