import sys
import requests
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TOOLSHED_API = "https://toolshed.g2.bx.psu.edu/api/repositories"
fn = sys.argv[1]

# The ToolShed rate-limits (429) when many new tools are checked at once; Retry honours Retry-After.
session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=Retry(
    total=5, backoff_factor=2, status_forcelist=(429, 502, 503, 504), raise_on_status=False,
)))


def load_tools(path):
    with open(path) as handle:
        data = yaml.safe_load(handle) or {}

    return {
        (tool["name"], tool["owner"])
        for tool in data.get("tools", [])
    }


def tool_exists(name, owner):
    response = session.get(
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
