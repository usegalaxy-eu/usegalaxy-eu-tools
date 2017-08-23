import yaml
import glob
for file in glob.glob("*.yaml"):
    print("Processing %s" % file)
    with open(file, 'r') as handle:
        w = yaml.load(handle)

    for tool in w['tools']:
        print(tool)
        if 'changeset_revision' not in tool:
            print(tool)

for file in glob.glob("*.yml"):
    print("Processing %s" % file)
    with open(file, 'r') as handle:
        w = yaml.load(handle)

    for tool in w['tools']:
        print(tool)
        if 'changeset_revision' not in tool:
            print(tool)
