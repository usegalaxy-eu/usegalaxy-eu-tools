#!/usr/bin/env python3
"""
Pre-filter YAML file to remove already-installed tools before calling shed-tools.
"""

import sys

import yaml


def format_tool_shed_url(url):
    if not url:
        return ""
    if not url.startswith("http"):
        url = f"https://{url}"
    if not url.endswith("/"):
        url = f"{url}/"
    return url


def load_yaml(filepath):
    with open(filepath, "r") as f:
        return yaml.safe_load(f)


def save_yaml(data, filepath):
    with open(filepath, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def main():
    if len(sys.argv) != 4:
        print("Usage: filter-installed.py <input.yaml> <installed.yaml> <output.yaml>")
        sys.exit(1)

    input_yaml = sys.argv[1]
    installed_yaml = sys.argv[2]
    output_yaml = sys.argv[3]

    input_data = load_yaml(input_yaml)
    installed_data = load_yaml(installed_yaml)

    if not installed_data:
        print("Warning: installed cache file is empty or invalid. Treating as no tools installed.")
        installed_data = {"tools": []}

    installed_tool_list = []
    for tool in installed_data.get("tools", []):
        name = tool.get("name")
        owner = tool.get("owner")

        for revision in tool.get("revisions", []):
            installed_tool_list.append((name, owner, revision))

    filtered_tools = []
    skipped_count = 0

    for tool in input_data.get("tools", []):
        name = tool.get("name")
        owner = tool.get("owner")

        new_revisions = []
        for revision in tool.get("revisions", []):
            if (name, owner, revision) not in installed_tool_list:
                new_revisions.append(revision)
            else:
                skipped_count += 1
                print(f"  Skipping already installed: {name} ({owner}) @ {revision}")

        if new_revisions:
            tool_copy = tool.copy()
            tool_copy["revisions"] = new_revisions
            filtered_tools.append(tool_copy)

    print(f"Skipped {skipped_count} already-installed revisions")
    print(f"Kept {len(filtered_tools)} tools with new revisions")

    output_data = input_data.copy()
    output_data["tools"] = filtered_tools

    save_yaml(output_data, output_yaml)
    print(f"Filtered YAML saved to {output_yaml}")


if __name__ == "__main__":
    main()
