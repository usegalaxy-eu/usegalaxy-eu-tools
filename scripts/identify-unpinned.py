import yaml
import glob
for file in glob.glob("*.yaml.lock"):
    print("Processing %s" % file)
    with open(file, 'r') as handle:
        w = yaml.load(handle)

    for tool in w['tools']:
        if 'changeset_revision' not in tool:
            print(tool)
