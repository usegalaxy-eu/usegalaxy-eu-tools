#!/usr/bin/env python3
"""
Sync IUC tools from galaxyproject/tools-iuc to tools_iuc.yaml.

This script discovers new tools in the IUC repository and automatically adds them
to tools_iuc.yaml with appropriate category mappings.
"""

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

import requests
import yaml


class IUCToolSyncer:
    def __init__(
        self,
        tools_yaml_path: Path,
        mapping_file_path: Path,
        iuc_repo_path: Path,
        github_token: Optional[str] = None,
        dry_run: bool = False,
    ):
        self.tools_yaml_path = tools_yaml_path
        self.mapping_file_path = mapping_file_path
        self.iuc_repo_path = iuc_repo_path
        self.github_token = github_token
        self.dry_run = dry_run

        # Load category mapping
        with open(mapping_file_path) as f:
            mapping_data = yaml.safe_load(f)
            self.category_mapping = mapping_data.get("mappings", {})

        # Load valid labels from schema
        schema_path = tools_yaml_path.parent / ".schema.yaml"
        with open(schema_path) as f:
            schema = yaml.safe_load(f)
            label_enum = schema["mapping"]["tools"]["sequence"][0]["mapping"][
                "tool_panel_section_label"
            ]["enum"]
            self.valid_labels = set(label_enum)
        # Case-insensitive fallback: valid_labels first, then explicit mappings override
        self.fallback_lower = {label.lower(): label for label in self.valid_labels}
        for key, value in self.category_mapping.items():
            self.fallback_lower[key.lower()] = value

        # Validate that all static mapping targets are valid labels
        for shed_cat, panel_label in self.category_mapping.items():
            if panel_label not in self.valid_labels:
                print(
                    f"Warning: Static mapping '{shed_cat}' -> '{panel_label}' target is not a valid panel label",
                    file=sys.stderr,
                )

        self.existing_tools: Set[Tuple[str, str]] = set()
        self.new_tools: List[Dict] = []
        self.report_lines: List[str] = []

    def load_existing_tools(self) -> None:
        """Load all existing tools from all YAML files in the repo to avoid duplicates."""
        yaml_files = list(self.tools_yaml_path.parent.glob("*.yaml"))

        for yaml_file in yaml_files:
            if yaml_file.name.endswith(".lock"):
                continue

            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                    if data and "tools" in data:
                        for tool in data["tools"]:
                            name = tool.get("name")
                            owner = tool.get("owner")
                            if name and owner:
                                self.existing_tools.add((name, owner))
            except Exception as e:
                print(f"Warning: Could not load {yaml_file}: {e}", file=sys.stderr)

    def parse_shed_yml(self, shed_yml_path: Path) -> Optional[Dict]:
        """Parse a .shed.yml file and extract tool metadata."""
        try:
            with open(shed_yml_path) as f:
                data = yaml.safe_load(f)

            if not data:
                return None

            name = data.get("name")
            owner = data.get("owner", "iuc")
            categories = data.get("categories", [])
            description = data.get("description", "")

            if not name:
                return None

            # Handle auto_tool_repositories (suite tools like bcftools)
            auto_tool_repos = data.get("auto_tool_repositories", {})
            if auto_tool_repos:
                name_template = auto_tool_repos.get("name_template", "{{ tool_id }}")
                tool_names = []
                tool_dir = shed_yml_path.parent

                for xml_file in tool_dir.glob("*.xml"):
                    tool_id = self._extract_tool_id(xml_file)
                    if tool_id:
                        # Apply name_template; handle any whitespace inside {{ tool_id }}
                        repo_name = re.sub(
                            r"\{\{\s*tool_id\s*\}\}", tool_id, name_template
                        )
                        # Skip if Jinja2 placeholders remain unresolved
                        if "{{" in repo_name or "}}" in repo_name:
                            continue
                        tool_names.append(repo_name)

                if tool_names:
                    return {
                        "suite": True,
                        "base_name": name,
                        "tool_names": tool_names,
                        "owner": owner,
                        "categories": categories,
                        "description": description,
                    }

            return {
                "suite": False,
                "name": name,
                "owner": owner,
                "categories": categories,
                "description": description,
            }
        except Exception as e:
            print(f"Warning: Could not parse {shed_yml_path}: {e}", file=sys.stderr)
            return None

    def _extract_tool_id(self, xml_file: Path) -> Optional[str]:
        """Extract the tool id from a Galaxy tool XML file.

        Returns None for non-tool XMLs (macros, test data, etc.).
        Resolves inline @TOKEN@ macros used in tool ids.
        """
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Only <tool> root elements are actual tools
            if root.tag != "tool":
                return None

            tool_id = root.get("id")
            if not tool_id:
                return None

            # Skip Jinja2-style template placeholders (these belong to suite templates)
            if "{{" in tool_id or "}}" in tool_id:
                return None

            # Resolve inline @TOKEN@ macros (e.g. bcftools_@EXECUTABLE@)
            if "@" in tool_id:
                for token in root.iter("token"):
                    token_name = token.get("name", "")
                    if token_name and token.text:
                        tool_id = tool_id.replace(token_name, token.text.strip())

                # If unresolved macros remain, skip this file
                if "@" in tool_id:
                    return None

            return tool_id
        except Exception:
            return None

    def scan_iuc_repo(self) -> List[Dict]:
        """Scan the IUC repo for all tools."""
        discovered_tools = []

        # Scan tools/ and data_managers/ directories
        for base_dir in ["tools", "data_managers"]:
            tools_dir = self.iuc_repo_path / base_dir
            if not tools_dir.exists():
                continue

            for shed_yml_path in tools_dir.rglob(".shed.yml"):
                # Skip deprecated tools
                if "deprecated" in shed_yml_path.parts:
                    continue

                is_data_manager = base_dir == "data_managers"
                tool_info = self.parse_shed_yml(shed_yml_path)
                if tool_info:
                    if tool_info.get("suite"):
                        # Handle suite tools
                        for tool_name in tool_info["tool_names"]:
                            discovered_tools.append(
                                {
                                    "name": tool_name,
                                    "owner": tool_info["owner"],
                                    "categories": tool_info["categories"],
                                    "description": tool_info["description"],
                                    "is_data_manager": is_data_manager,
                                }
                            )
                    else:
                        # Regular tool
                        discovered_tools.append(
                            {
                                "name": tool_info["name"],
                                "owner": tool_info["owner"],
                                "categories": tool_info["categories"],
                                "description": tool_info["description"],
                                "is_data_manager": is_data_manager,
                            }
                        )

        return discovered_tools

    def map_category_static(self, categories: List[str]) -> Optional[str]:
        """Map categories using static mapping file. Returns first match."""
        # 1. Exact explicit mapping
        for category in categories:
            if category in self.category_mapping:
                return self.category_mapping[category]
        # 2. Case-insensitive fallback (explicit mapping keys + valid_labels)
        for category in categories:
            lower = category.lower()
            if lower in self.fallback_lower:
                return self.fallback_lower[lower]
        return None

    def map_category_ai(self, tools: List[Dict]) -> Dict[str, Tuple[str, str]]:
        """
        Use GitHub Models API to guess best category for unmapped tools.

        Returns: dict mapping tool name to (label, reason)
        """
        if not self.github_token:
            print(
                "Warning: No GitHub token available for AI category mapping",
                file=sys.stderr,
            )
            return {}

        if not tools:
            return {}

        # Process in batches to avoid token limit overflows
        batch_size = 25
        all_mappings: Dict[str, Tuple[str, str]] = {}
        for batch_start in range(0, len(tools), batch_size):
            batch = tools[batch_start : batch_start + batch_size]
            batch_mappings = self._map_category_ai_batch(batch)
            all_mappings.update(batch_mappings)

        return all_mappings

    def _map_category_ai_batch(self, tools: List[Dict]) -> Dict[str, Tuple[str, str]]:
        """Send a single batch of tools to the AI API for category mapping."""
        tools_info = [
            {
                "name": tool["name"],
                "description": tool["description"],
                "categories": tool["categories"],
            }
            for tool in tools
        ]

        prompt = f"""You are a Galaxy tool categorization expert. Given a list of bioinformatics tools with their metadata, assign each tool to the SINGLE MOST APPROPRIATE category from the provided list of valid panel section labels.

Valid panel section labels:
{", ".join(sorted(self.valid_labels))}

Tools to categorize:
{json.dumps(tools_info, indent=2)}

For each tool, respond with a JSON array of objects with this structure:
[
  {{
    "name": "tool_name",
    "label": "chosen_label",
    "reason": "brief explanation"
  }},
  ...
]

Important:
- Choose ONLY from the valid panel section labels provided above
- Pick the SINGLE best match for each tool
- If uncertain, prefer more general categories like "Other Tools"
- Base decisions on tool name, description, and ToolShed categories"""

        try:
            response = requests.post(
                "https://models.github.ai/inference/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.github_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that categorizes bioinformatics tools. Always respond with valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                },
                timeout=60,
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Parse JSON response
            # Try to extract JSON if it's wrapped in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            mappings_list = json.loads(content)

            # Convert to dict
            mappings: Dict[str, Tuple[str, str]] = {}
            for item in mappings_list:
                tool_name = item["name"]
                label = item["label"]
                reason = item.get("reason", "AI suggested")

                # Validate label
                if label in self.valid_labels:
                    mappings[tool_name] = (label, reason)
                else:
                    print(
                        f"Warning: AI suggested invalid label '{label}' for {tool_name}, using 'Other Tools'",
                        file=sys.stderr,
                    )
                    mappings[tool_name] = (
                        "Other Tools",
                        f"AI suggested invalid label: {label}",
                    )

            return mappings

        except Exception as e:
            print(f"Warning: AI category mapping failed: {e}", file=sys.stderr)
            return {}

    def compute_new_tools(self, discovered_tools: List[Dict]) -> None:
        """Compute which tools are new and need to be added."""
        for tool in discovered_tools:
            name = tool["name"]
            owner = tool["owner"]

            # Check if tool already exists
            if (name, owner) in self.existing_tools:
                continue

            # Data managers don't get a label (detected by directory or name prefix)
            if tool.get("is_data_manager") or name.startswith("data_manager"):
                self.new_tools.append(
                    {
                        "name": name,
                        "owner": owner,
                        "label": None,
                        "mapping_source": "data_manager",
                        "categories": tool["categories"],
                        "description": tool["description"],
                    }
                )
            else:
                # Try static mapping first
                label = self.map_category_static(tool["categories"])
                if label:
                    self.new_tools.append(
                        {
                            "name": name,
                            "owner": owner,
                            "label": label,
                            "mapping_source": "static",
                            "categories": tool["categories"],
                            "description": tool["description"],
                        }
                    )
                else:
                    # Will need AI mapping
                    self.new_tools.append(
                        {
                            "name": name,
                            "owner": owner,
                            "label": None,
                            "mapping_source": "unmapped",
                            "categories": tool["categories"],
                            "description": tool["description"],
                        }
                    )

    def apply_ai_mapping(self) -> None:
        """Apply AI mapping to unmapped tools."""
        unmapped_tools = [
            t for t in self.new_tools if t["mapping_source"] == "unmapped"
        ]

        if not unmapped_tools:
            return

        print(
            f"Attempting AI mapping for {len(unmapped_tools)} unmapped tools...",
            file=sys.stderr,
        )

        ai_mappings = self.map_category_ai(unmapped_tools)

        for tool in self.new_tools:
            if tool["mapping_source"] == "unmapped":
                if tool["name"] in ai_mappings:
                    label, reason = ai_mappings[tool["name"]]
                    tool["label"] = label
                    tool["mapping_source"] = "ai"
                    tool["ai_reason"] = reason
                else:
                    # Fallback
                    tool["label"] = "Other Tools"
                    tool["mapping_source"] = "fallback"

    def append_to_yaml(self) -> None:
        """Append new tools to tools_iuc.yaml as formatted text."""
        if not self.new_tools:
            return

        # Prepare new entries
        timestamp = datetime.now().strftime("%Y-%m-%d")
        new_entries = [f"\n# Tools added by sync-iuc-tools.py on {timestamp}\n"]

        for tool in self.new_tools:
            new_entries.append(f"  - name: {tool['name']}\n")
            new_entries.append(f"    owner: {tool['owner']}\n")
            if tool["label"]:
                new_entries.append(f"    tool_panel_section_label: '{tool['label']}'\n")
            new_entries.append("\n")

        # Append to file
        if not self.dry_run:
            with open(self.tools_yaml_path, "a") as f:
                f.writelines(new_entries)

            # Validate that the resulting file is still valid YAML
            try:
                with open(self.tools_yaml_path) as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(
                    f"Error: YAML validation failed after writing: {e}", file=sys.stderr
                )
                raise

    def generate_report(self) -> str:
        """Generate markdown report for PR body."""
        lines = ["# IUC Tools Sync Report\n"]
        lines.append(f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n")
        lines.append(f"\n**Total new tools found:** {len(self.new_tools)}\n")

        if not self.new_tools:
            lines.append("\nNo new tools to add.\n")
            return "".join(lines)

        # Group by mapping source
        static_mapped = [t for t in self.new_tools if t["mapping_source"] == "static"]
        ai_mapped = [t for t in self.new_tools if t["mapping_source"] == "ai"]
        data_managers = [
            t for t in self.new_tools if t["mapping_source"] == "data_manager"
        ]
        fallback = [t for t in self.new_tools if t["mapping_source"] == "fallback"]

        if static_mapped:
            lines.append(f"\n## Statically Mapped Tools ({len(static_mapped)})\n")
            lines.append(
                "\nThese tools were automatically categorized using the static mapping file.\n"
            )
            lines.append("\n| Tool Name | Panel Section | ToolShed Categories |\n")
            lines.append("|-----------|---------------|--------------------|\n")
            for tool in sorted(static_mapped, key=lambda t: t["name"]):
                cats = ", ".join(tool["categories"]) if tool["categories"] else "None"
                lines.append(f"| `{tool['name']}` | {tool['label']} | {cats} |\n")

        if ai_mapped:
            lines.append(f"\n## AI-Suggested Categories ({len(ai_mapped)})\n")
            lines.append(
                "\n⚠️ **These tools were categorized using AI.** Please review and adjust if needed.\n"
            )
            lines.append(
                "\n| Tool Name | Suggested Panel Section | Reason | ToolShed Categories |\n"
            )
            lines.append(
                "|-----------|------------------------|--------|--------------------|\\n"
            )
            for tool in sorted(ai_mapped, key=lambda t: t["name"]):
                cats = ", ".join(tool["categories"]) if tool["categories"] else "None"
                reason = tool.get("ai_reason", "AI suggested")
                lines.append(
                    f"| `{tool['name']}` | {tool['label']} | {reason} | {cats} |\n"
                )

        if data_managers:
            lines.append(f"\n## Data Managers ({len(data_managers)})\n")
            lines.append(
                "\nThese are data managers and don't require a panel section label.\n"
            )
            lines.append("\n| Tool Name |\n")
            lines.append("|-----------|\n")
            for tool in sorted(data_managers, key=lambda t: t["name"]):
                lines.append(f"| `{tool['name']}` |\n")

        if fallback:
            lines.append(f"\n## Fallback Categorization ({len(fallback)})\n")
            lines.append(
                "\n⚠️ **These tools could not be categorized** (static mapping failed and AI unavailable). Assigned to 'Other Tools'.\n"
            )
            lines.append("\n| Tool Name | ToolShed Categories |\n")
            lines.append("|-----------|--------------------|\\n")

            for tool in sorted(fallback, key=lambda t: t["name"]):
                cats = ", ".join(tool["categories"]) if tool["categories"] else "None"
                lines.append(f"| `{tool['name']}` | {cats} |\n")

        lines.append("\n---\n")
        lines.append(
            "\n🤖 This PR was automatically generated by the `sync-iuc-tools` workflow.\n"
        )

        return "".join(lines)

    def run(self, report_file: Optional[Path] = None) -> int:
        """Main execution flow."""
        print("Loading existing tools from all YAML files...", file=sys.stderr)
        self.load_existing_tools()
        print(f"Found {len(self.existing_tools)} existing tools", file=sys.stderr)

        print(f"Scanning IUC repository at {self.iuc_repo_path}...", file=sys.stderr)
        discovered_tools = self.scan_iuc_repo()
        print(f"Discovered {len(discovered_tools)} tools in IUC repo", file=sys.stderr)

        print("Computing new tools...", file=sys.stderr)
        self.compute_new_tools(discovered_tools)
        print(f"Found {len(self.new_tools)} new tools", file=sys.stderr)

        if self.new_tools:
            print("Applying AI mapping to unmapped tools...", file=sys.stderr)
            self.apply_ai_mapping()

            if not self.dry_run:
                print(
                    f"Appending new tools to {self.tools_yaml_path}...", file=sys.stderr
                )
                self.append_to_yaml()
            else:
                print("DRY RUN: Would append new tools to YAML", file=sys.stderr)

        # Generate report
        report = self.generate_report()

        if report_file:
            report_file.write_text(report)
            print(f"Report written to {report_file}", file=sys.stderr)
        else:
            print("\n" + report)

        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Sync IUC tools from galaxyproject/tools-iuc to tools_iuc.yaml"
    )
    parser.add_argument(
        "--tools-yaml",
        type=Path,
        required=True,
        help="Path to tools_iuc.yaml file",
    )
    parser.add_argument(
        "--mapping-file",
        type=Path,
        required=True,
        help="Path to category-mapping.yml file",
    )
    parser.add_argument(
        "--iuc-repo-path",
        type=Path,
        required=True,
        help="Path to cloned galaxyproject/tools-iuc repository",
    )
    parser.add_argument(
        "--github-token",
        type=str,
        help="GitHub token for API access (or set GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't modify files, just show what would be done",
    )
    parser.add_argument(
        "--report-file",
        type=Path,
        help="Path to write markdown report",
    )

    args = parser.parse_args()

    # Get GitHub token from arg or env
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")

    syncer = IUCToolSyncer(
        tools_yaml_path=args.tools_yaml,
        mapping_file_path=args.mapping_file,
        iuc_repo_path=args.iuc_repo_path,
        github_token=github_token,
        dry_run=args.dry_run,
    )

    return syncer.run(report_file=args.report_file)


if __name__ == "__main__":
    sys.exit(main())
