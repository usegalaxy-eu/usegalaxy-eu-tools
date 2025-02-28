import yaml
import sys
import argparse
import copy

def load_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def merge_tools(*yaml_files):
    merged_tools = {}
    for yaml_file in yaml_files:
        tools_yaml = load_yaml(yaml_file)
        for tool in tools_yaml['tools']:
            merged_tools[tool['name']] = tool
    return {'tools': list(merged_tools.values())}

def main():
    parser = argparse.ArgumentParser(description='Merge and compare Galaxy tool YAML files.')
    parser.add_argument('--current', required=True, help='Path to current_galaxy_tools.yaml')
    parser.add_argument('--tools_iuc', required=True, help='Path to tools_iuc.yaml')
    parser.add_argument('--belgium_custom', required=True, help='Path to belgium-custom.yaml')
    parser.add_argument('--gtn_tutorials', required=True, help='Path to GTN_tutorials_tools.yaml')
    args = parser.parse_args()

    current_tools = load_yaml(args.current)
    merged_tools = merge_tools(args.tools_iuc, args.belgium_custom, args.gtn_tutorials)

    current_tool_names = {tool['name'] for tool in current_tools['tools']}
    merged_tool_names = {tool['name'] for tool in merged_tools['tools']}

    only_in_current = current_tool_names - merged_tool_names
    only_in_merged = merged_tool_names - current_tool_names

    print("Tools only in current_galaxy_tools.yaml:")
    for tool in only_in_current:
        print(tool)

    print("\nTools only in merged tools YAML files:")
    for tool in only_in_merged:
        print(tool)

if __name__ == "__main__":
    main()