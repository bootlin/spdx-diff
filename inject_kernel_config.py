#!/usr/bin/env python3
import json
import argparse
from datetime import datetime, timezone


def parse_config_file(config_path):
    entries = []
    with open(config_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or (line.startswith("#") and "is not set" not in line):
                continue
            if line.startswith("# CONFIG_") and "is not set" in line:
                key = line.split()[1]
                value = "n"
            elif "=" in line:
                key, value = line.split("=", 1)
            else:
                continue
            entries.append({
                "type": "DictionaryEntry",
                "key": key.strip(),
                "value": value.strip('" \t\n\r')
            })
    return entries

def get_creation_info_from_package(pkg_obj):
    return pkg_obj.get("creationInfo") or "_:CreationInfoDefault"

def find_kernel_package(graph):
    for obj in graph:
        if obj.get("type") == "software_Package":
            description = obj.get("description", "").strip().lower()
            if description == "linux kernel.":
                return obj
    raise ValueError("No software_Package with description 'Linux kernel.' found.")

def main():
    parser = argparse.ArgumentParser(description="Add kernel make build using .config as parameters, linked to kernel package with SPDX IRIs")
    parser.add_argument("--spdx", required=True, help="Input SPDX 3.0 JSON file")
    parser.add_argument("--config", required=True, help="Linux kernel .config file")
    parser.add_argument("--output", required=True, help="Output SPDX 3.0 JSON file (modified)")
    args = parser.parse_args()

    with open(args.spdx, "r") as f:
        spdx_data = json.load(f)

    graph = spdx_data.get("@graph", [])

    # Step 1: Find the kernel package
    kernel_pkg = find_kernel_package(graph)
    kernel_pkg_id = kernel_pkg["spdxId"]

    # Step 2: Derive full build_Build SPDX ID
    base_doc_uri = kernel_pkg_id.split("/spdxdocs/")[0]
    doc_id_part = kernel_pkg_id.split("/spdxdocs/")[1].split("/")[0]
    kernel_build_id = f"{base_doc_uri}/spdxdocs/{doc_id_part}/build/kernel-make"

    # Step 3: Link to existing creationInfo
    creation_info_id = get_creation_info_from_package(kernel_pkg)

    # Step 4: Parse kernel config
    kernel_config = parse_config_file(args.config)

    kernel_build = {
        "type": "build_Build",
        "spdxId": kernel_build_id,
        "creationInfo": creation_info_id,
        "name": "kernel-make",
        "build_buildType": "http://openembedded.org/bitbake/do_create_spdx/kernel-make",
        "build_parameter": kernel_config,
    }
    graph.append(kernel_build)

    # Step 5: Add relationship from kernel package to its build
#    graph.append({
#        "type": "Relationship",
#        "relationshipType": "hasInput",
#        "from": kernel_pkg_id,
#        "to": [kernel_build_id]
#    })

    spdx_data["@graph"] = graph

    with open(args.output, "w") as f:
        json.dump(spdx_data, f, indent=2)


if __name__ == "__main__":
    main()
