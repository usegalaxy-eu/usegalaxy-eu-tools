import json
import yaml
import glob
from collections import OrderedDict


# https://stackoverflow.com/questions/42518067/how-to-use-ordereddict-as-an-input-in-yaml-dump-or-yaml-safe-dump
def dump_ordered_yaml(ordered_data, output_filename, Dumper=yaml.Dumper):
    class OrderedDumper(Dumper):
        pass

    class UnsortableList(list):
        def sort(self, *args, **kwargs):
            pass

    class UnsortableOrderedDict(OrderedDict):
        def items(self, *args, **kwargs):
            return UnsortableList(OrderedDict.items(self, *args, **kwargs))

    OrderedDumper.add_representer(UnsortableOrderedDict, yaml.representer.SafeRepresenter.represent_dict)
    with open(output_filename, "w") as f:
        yaml.dump(ordered_data, f, Dumper=OrderedDumper)


with open('tsr.json', 'r') as handle:
    data = json.load(handle)

t = {}
for x in data:
    t[(x['owner'], x['name'])] = x['changeset_revision']


for file in glob.glob("*.yaml"):
    with open(file, 'r') as handle:
        w = yaml.load(handle)

    for tool in w['tools']:
        key = (tool['owner'], tool['name'])
        if key in t:
            tool['changeset_revision'] = str(t[key])

    with open(file, 'w') as handle:
        yaml.dump(w, handle, default_flow_style=False)
