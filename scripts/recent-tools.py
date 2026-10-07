#!/usr/bin/env python3
"""Extract tools that changed recently in a lock file, for incremental installs.

Parses `git log --patch` for the given lock file and selects tools whose
revision list gained new revisions (or that were added as new entries).
Tools whose entries were only removed or renamed are not selected, since
shed-tools install can only add tools. If the lock file has no git history,
all tools are considered recent. Writes the filtered lock file to --output
only when at least one tool matches; otherwise nothing is written so the
caller can skip the installation entirely.
"""
import argparse
import re
import subprocess
import sys

import yaml

NAME_RE = re.compile(r"^[ +-]- name: (\S+)")
ADDED_REVISION_RE = re.compile(r"^\+  - ([0-9a-f]{12,16})\s*$")


def recent_tools(fn, since):
    """Return the set of tool names with new revisions, or None for 'all tools'."""
    try:
        log = subprocess.run(
            ["git", "log", f"--since={since}", "--patch", "--", fn],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError as exc:
        print(
            f"git log failed for {fn} ({exc.stderr.strip()}); treating all tools as recent",
            file=sys.stderr,
        )
        return None

    recent = set()
    current = None
    for line in log.splitlines():
        name_match = NAME_RE.match(line)
        if name_match:
            current = name_match.group(1)
            continue
        if ADDED_REVISION_RE.match(line) and current:
            recent.add(current)
    return recent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fn", help="Lock file (.yaml.lock) to filter")
    parser.add_argument("--since", default="4 weeks", help="Git time window, e.g. '4 weeks'")
    parser.add_argument("--output", help="Path of the filtered lock file to write")
    args = parser.parse_args()

    with open(args.fn) as handle:
        lockfile = yaml.safe_load(handle)

    recent = recent_tools(args.fn, args.since)
    if recent is None:
        tools = lockfile.get("tools", [])
    else:
        tools = [tool for tool in lockfile.get("tools", []) if tool.get("name") in recent]

    if not tools:
        if not args.output:
            print(f"No tools changed in {args.fn} within '{args.since}', skipping")
        return

    if args.output:
        output = {key: value for key, value in lockfile.items() if key != "tools"}
        output["tools"] = tools
        with open(args.output, "w") as handle:
            yaml.dump(output, handle, default_flow_style=False)
        print(f"Wrote {len(tools)} recently changed tool(s) from {args.fn} to {args.output}")
    else:
        print(f"{len(tools)} recently changed tool(s) in {args.fn}:")
        for tool in tools:
            print(f"- {tool['name']}")


if __name__ == "__main__":
    main()
