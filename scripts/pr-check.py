import sys
import requests
import yaml

TOOLSHED_API = "https://toolshed.g2.bx.psu.edu/api/repositories"
fn = sys.argv[1]


def load_tools(path):
    with open(path) as handle:
        data = yaml.safe_load(handle) or {}

    return {
        (tool["name"], tool["owner"])
        for tool in data.get("tools", [])
    }


def tool_exists(name, owner):
    response = requests.get(
        TOOLSHED_API,
        params={"name": name, "owner": owner, "page_size": 1},
        timeout=30,
    )
    response.raise_for_status()

    return any(
        repo["name"] == name and repo.get("owner") == owner
        for repo in response.json()
    )

# never mind about fancy yaml linting, let's just make sure the files are openable
sys.stdout.write('Checking modified yaml file {}...\n'.format(fn))
yml = load_tools(fn)
yml_lock = load_tools('{}.lock'.format(fn))

new_tools = sorted(yml - yml_lock)

for (name, owner) in new_tools:  # check all new tools are in the tool shed
    sys.stdout.write(
        'Checking new tool {}/{} is in the toolshed...\n'.format(owner, name)
    )
    assert tool_exists(name, owner), '{}/{} not in toolshed.'.format(owner, name)
