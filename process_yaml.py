import yaml
import sys
import argparse

section_labels_list = [
   'Get Data', 'Send Data', 'Collection Operations', 'Expression Tools',
   'Text Manipulation', 'Filter and Sort', 'Join, Subtract and Group',
   'Convert Formats', 'FASTA/FASTQ', 'FASTQ Quality Control', 'SAM/BAM', 'BED',
   'VCF/BCF', 'Nanopore', 'Operate on Genomic Intervals', 'Fetch Sequences / Alignments',
   'Annotation', 'Ontology', 'Assembly', 'Mapping', 'Variant Calling', 'Genome editing',
   'RNA-Seq', 'Peak Calling', 'Epigenetics', 'Phylogenetics', 'Phenotype Association',
   'Single-cell', 'Get scRNAseq data', 'Seurat', 'SC3', 'Scanpy', 'Monocl3', 'SCMap',
   'SCCAF', 'Single Cell Utils and Viz', 'Picard', 'deepTools', 'Gemini', 'EMBOSS',
   'GATK Tools', 'NCBI Blast', 'HiCExplorer', 'RAD-seq', 'GraphClust' , 'MiModD',
   'Metagenomic Analysis', 'Qiime' , 'Mothur' , 'DNA Metabarcoding' , 'Proteomics', 'Metabolomics',
   'ChemicalToolBox', 'Statistics', 'Graph/Display Data' , 'Evolution', 'Motif Tools', "Machine Learning",
   'Test Tools', 'GIS Data Handling', 'Animal Detection on Acoustic Recordings', 'Imaging', 'Virology',
   'Regional Variation' , 'Genome Diversity' , 'Deprecated', 'Interactive tools', 'Apollo', 'Quality Control',
   'Multiple Alignments', 'Climate Analysis', 'RNA Analysis', 'Data Managers', 'Extract Features', 'Other Tools',
   'Species abundance' ]

section_ids_list =  [ "get_data", "send_data", "collection_operations", "expression_tools", "text_manipulation",
                    "filter_and_sort", "join__subtract_and_group", "convert_formats", "fasta_fastq", "fastq_quality_control",
                       "sam_bam", "bed", "vcf_bcf", "nanopore", "operate_on_genomic_intervals", "fetch_sequences___alignments",
                        "annotation", "ontology", "assembly", "mapping", "variant_calling", "genome_editing", "rna_seq",
                        "peak_calling", "epigenetics", "phylogenetics", "phenotype_association", "single-cell",
                        "hca_sc_get-scrna", "hca_sc_seurat_tools", "hca_sc_sc3_tools", "hca_sc_scanpy_tools", 
                        "hca_sc_label_analysis_tools", "hca_sc_garnett_tools", "hca_sc_scpred_tools", "hca_sc_scater_tools", "machine_learning",
                        "hca_sc_monocle3_tools", "hca_sc_scmap_tools", "hca_sc_sccaf_tools", "hca_sc_utils_viz", "picard",
                        "deeptools", "gemini", "emboss", "gatk_tools", "ncbi_blast", "hicexplorer", "rad_seq", "graphclust",
                        "mimodd", "metagenomic_analysis", "qiime", "mothur", "dna_metabarcoding" , "proteomics", "metabolomics", "chemicaltoolbox",
                        "statistics", "graph_display_data", "evolution", "motif_tools", "test_tools", "gis_data_handling", "quality_control",
                        "animal_detection_on_acoustic_recordings", "regional_variation", "genome_diversity", 'apollo', 'imaging', 'virology',
                        "deprecated", "interactivetools", "multiple_alignments", "climate_analysis", "rna_analysis", "species_abundance"]


def lint_file(tools_yaml):
    """
    Check that the section labels or ids are part of the standard lists
    """
    for tool in tools_yaml['tools']:
        if 'tool_panel_section_label' in tool.keys():
            if tool['tool_panel_section_label'] not in section_labels_list:
                print(f"This label is not in the list: {tool['tool_panel_section_label']}")
        else:
            if tool['tool_panel_section_id'] not in section_ids_list:
                print(f"This id is not in the list {tool['tool_panel_section_id']}")

def get_latest_only(tools_yaml):
    """
    Parse a dict with a list of tools and return only the latest revision
    Used to create a base set of tools and versions when deploying a new server from scratch
    """
    tools_list = []

    for tool in tools_yaml['tools']:
        new_entry = {}
        new_entry['name'] = tool['name']
        new_entry['owner'] = tool['owner']
        new_entry['revisions'] = [tool['revisions'][0]]
        if 'tool_panel_section_label' in tool.keys():
            new_entry['tool_panel_section_label'] = tool['tool_panel_section_label']
            if new_entry['tool_panel_section_label'] not in section_labels_list:
                print(f"This label is not in the list {new_entry['tool_panel_section_label']}")
        else:
            new_entry['tool_panel_section_id'] = tool['tool_panel_section_id']
            if new_entry['tool_panel_section_id'] not in section_ids_list:
                print(f"This label is not in the list {new_entry['tool_panel_section_id']}")
        tools_list.append(new_entry)

    ret_dict = {'install_repository_dependencies': True,
                'install_resolver_dependencies': True,
                'install_tool_dependencies': True,
                'tools': tools_list
                }
    return ret_dict


def add_sections(base_dict, new_tools):
    """
    Take a base_dict (reference) containing a (reference) set of tools,
    and a set of new_tools. Add the missing section labels in the tools from the new_tools
    that are already in the base(reference)
    Also change the section_labels when the one in new_tools is not the same as base_dict
    """
    base_tools_labels = {}
    # load base tools list in dict
    for tool in base_dict['tools']:
        if 'tool_panel_section_label' in tool.keys():
            if tool['name'] not in base_tools_labels.keys():
                base_tools_labels[tool['name']] = [tool['tool_panel_section_label']]
            else:
                base_tools_labels[tool['name']].append(tool['tool_panel_section_label'])

    # iterate over the new tools and update sections in place
    for tool in new_tools['tools']:
        if tool['name'] in base_tools_labels.keys():
            if 'tool_panel_section_label' in tool.keys():
                # new tool already has a label
                if tool['tool_panel_section_label'] not in base_tools_labels[tool['name']]:
                    # the label is not in the list of possible ones.
                    # Update
                    tool['tool_panel_section_label'] = base_tools_labels[tool['name']][0]
            else:
                # assign the first of the possible labels
                tool['tool_panel_section_label'] = base_tools_labels[tool['name']][0]

    return new_tools


def update_revisions(tool_key, base_revisions_list, updated_revisions_list):
    new_revisions_list = []
    # first entries in the updated list are the new ones
    for rev in updated_revisions_list:
        new_revisions_list.append(rev)
        if rev in base_revisions_list['revisions']:
            print(f"existing revision for tool {tool_key}")
            return new_revisions_list
    return new_revisions_list


def update_from_base(base_dict, updated_dict):
    """
    Takes a dict with a base list of tools and revisions and an updated one.
    Prints a list with the tools and revisions from the base lists plus:
        - the newer revisions of the tools included in the base
        - the extra tools in the updated one (including only the latest revision)
    """
    tools_list = []
    updated_names = []
    base_tools = {}
    # load base tools list in dict
    for tool in base_dict['tools']:
        # print(f"Tool name is {tool['name']}")
        # Just alert of duplicated entries, but keep the last entry
        if 'tool_panel_section_label' in tool.keys():
            entry_key = tool['name'] + '_' + tool['tool_panel_section_label']
        else:
            entry_key = tool['name'] + '_' + tool['tool_panel_section_id']
        if entry_key in base_tools.keys():
            # print(entry_key)
            print(f'Duplicated entry key in base tool list: {entry_key}')
        base_tools[entry_key] = tool

    # iterate over the updated list
    for tool in updated_dict['tools']:
        new_entry = {}
        new_entry['name'] = tool['name']
        new_entry['owner'] = tool['owner']
        if 'tool_panel_section_label' in tool.keys():
            dict_key = tool['name'] + '_' + tool['tool_panel_section_label']
        else:
            dict_key = tool['name'] + '_' + tool['tool_panel_section_id']
        if dict_key in base_tools.keys():
            print(base_tools[dict_key],tool['revisions'])
            new_entry['revisions'] = update_revisions(dict_key, base_tools[dict_key],
                                                      tool['revisions'])
        else:
            new_entry['revisions'] = [tool['revisions'][0]]

        # some tool entries dont define a tool_panel_section_label but a  tool_panel_section_id
        # assert new_entry['tool_panel_section_label'] in section_labels_list
        if 'tool_panel_section_label' in tool.keys():
            new_entry['tool_panel_section_label'] = tool['tool_panel_section_label']
        else:
            if 'tool_panel_section_id' in tool.keys():
                new_entry['tool_panel_section_id'] = tool['tool_panel_section_id']
            else:
                sys.exit(f"No panel definition for tool {tool['name']}")

        # store the names of the udpated tools
        updated_names.append(new_entry['name'])

        tools_list.append(new_entry)

    for tool in base_dict['tools']:
        if tool['name'] not in updated_names:
            tools_list.append(tool)

    ret_dict = {
        'install_repository_dependencies': True,
        'install_resolver_dependencies': True,
        'install_tool_dependencies': False,
        'tools': tools_list
    }
    return ret_dict


def update_revision_from_base(base_dict, updated_dict):
    """
    Takes a dict with a base list of tools and revisions and an updated one.
    Prints a list with the tools and revisions from the base lists plus:
        - the latest revision of the tools included in the base
    """
    updated_tools_list = []
    # load base tools list in dict
    tools_list = []
    tools_list_eu = []  
    for i in base_dict['tools']:
        tools_list.append({j:i[j] for j in i if j != 'revisions'})
    
    for i in updated_dict['tools']:
        tools_list_eu.append({j:i[j] for j in i if j != 'revisions'})

    
    for tool, rev  in zip(tools_list, base_dict['tools']):
        # print(i)
        # print(j)
        if tool in tools_list_eu:
            i = tools_list_eu.index(tool)
            # print(updated_dict['tools'][i]['revisions'], rev['revisions'])
            if updated_dict['tools'][i]['revisions'][0] not in rev['revisions']:
                # print(i)
                rev['revisions'].insert(0, updated_dict['tools'][i]['revisions'][0])
        updated_tools_list.append(rev)

    ret_dict = {
        'install_repository_dependencies': True,
        'install_resolver_dependencies': True,
        'install_tool_dependencies': False,
        'tools': updated_tools_list
    }
    return ret_dict



if __name__ == '__main__':

    argparser = argparse.ArgumentParser(description='Arguments to parse.')
    argparser.add_argument('--update', action='store_true', help='Update from a base file')
    argparser.add_argument('--revision_only', action='store_true', help='Only update revisions from a base file')
    argparser.add_argument('--add_sections', action='store_true', help='Add/update sections labels when possible using a base (reference) file')
    argparser.add_argument('--lint', action='store_true', help='Lint the section labels/ids')
    argparser.add_argument('--tools_yaml', '-y', dest='tools_yaml', type=str, required=True,
                        help='Required file with full/updated set of tools')
    argparser.add_argument('--base_file', '-b', dest='base_file_path', type=str,
                        help='File to use as base reference when running with update True')
    argparser.add_argument('--out_file', '-o', type=str,
                        help='File to use as base reference when running with update True')
    args = argparser.parse_args()


    # Common use cases:
    #   Merge contents of a tools yaml file with another:
    #   process_yaml.py --update --base_file base.yaml.lock --tools_yaml new.yaml.lock -o merge_updated.yaml.lock



    # Load updated/full file contents
    tools_file = open(args.tools_yaml)
    tools_yaml = yaml.load(tools_file)

    if args.update:
        base_file = open(args.base_file_path)
        base_yaml = yaml.load(base_file)
        parsed_dict = update_from_base(base_yaml, tools_yaml)
    elif args.revision_only:
        base_file = open(args.base_file_path)
        base_yaml = yaml.load(base_file)
        parsed_dict = update_revision_from_base(base_yaml, tools_yaml)
    else:
        if args.lint:
            lint_file(tools_yaml)
        else:
            if args.add_sections:
                base_file = open(args.base_file_path)
                base_yaml = yaml.load(base_file)
                parsed_dict = add_sections(base_yaml, tools_yaml)
            else:
                parsed_dict = get_latest_only(tools_yaml)

    if not args.lint:
        with open(args.out_file, 'w') as outfile:
            yaml.dump(parsed_dict, outfile, default_flow_style=False)
