import sys
import yaml

from bioblend import toolshed 

ts = toolshed.ToolShedInstance(url='https://toolshed.g2.bx.psu.edu')
fn = sys.argv[1]

# never mind about fancy yaml linting, let's just make sure the files are openable
sys.stdout.write('Checking modified yaml file {}...\n'.format(fn))
with open(fn) as f: 
    yml = [n['name'] for n in yaml.safe_load(f)['tools']]

with open('{}.lock'.format(fn)) as f:
    yml_lock = [n['name'] for n in yaml.safe_load(f)['tools']]

new_tools = [n for n in yml if n not in yml_lock]

for tool in new_tools[1:]:  # check all new tools are in the tool shed
    print(tool)
    sys.stdout.write('Checking new tool {} is in the toolshed...\n'.format(tool))
    total_hits = ts.repositories.search_repositories(tool)["total_results"]
    print(total_hits)
    search_hits = [hit['repository']['name'] for hit in ts.repositories.search_repositories(tool,page_size=380)['hits']]
    print(search_hits)
    #search_hits = iter(ts.repositories.search_repositories(tool)['hits'])
    #for hit in search_hits:
    #    print(hit)
    assert tool in search_hits, '{} not in toolshed.'.format(tool)
