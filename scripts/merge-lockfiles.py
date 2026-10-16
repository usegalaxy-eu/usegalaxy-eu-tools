#!/usr/bin/env python3
"""Merge lock files into one tools file for a single shed-tools run.

shed-tools looks up everything installed on the server once per run, so one
run for all lock files does that lookup once instead of once per lock file.
Each lock file's install_* settings are copied onto its tools, so the tools
are installed exactly as they would be from their own lock file.
"""
import argparse

import yaml

FLAGS = ("install_repository_dependencies", "install_resolver_dependencies", "install_tool_dependencies")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lockfiles", nargs="+", help="Lock files (.yaml.lock) to merge, in install order")
    parser.add_argument("--output", required=True, help="Path of the merged tools file to write")
    args = parser.parse_args()

    tools = []
    for fn in args.lockfiles:
        with open(fn) as handle:
            lockfile = yaml.safe_load(handle) or {}
        for tool in lockfile.get("tools") or []:
            for flag in FLAGS:
                # same rule as shed-tools: the tool's own value, else the lock file's
                tool[flag] = bool(tool.get(flag) or lockfile.get(flag))
            tools.append(tool)

    with open(args.output, "w") as handle:
        yaml.dump({"tools": tools}, handle, default_flow_style=False)
    print(f"Merged {len(tools)} tools from {len(args.lockfiles)} lock files into {args.output}")


if __name__ == "__main__":
    main()
