import yaml
import os
import glob
import copy

from bioblend import toolshed


ts = toolshed.ToolShedInstance(url='https://toolshed.g2.bx.psu.edu')
TRUSTED_AUTHORS = (
    'iuc',
)

TRUSTED_REPOSITORIES = (
    # (owner, repo_name)
    ("bgruening", "sailfish"),
    ("bgruening", "salmon"),
    ("bgruening", "suite_hicexplorer"),
    ("crs4", "prokka"),
    ("crs4", "taxonomy_krona_chart"),
    ("devteam", "add_value"),
    ("devteam", "annotation_profiler"),
    ("devteam", "bam_to_sam"),
    ("devteam", "bamleftalign"),
    ("devteam", "bamtools"),
    ("devteam", "bamtools_filter"),
    ("devteam", "bamtools_split"),
    ("devteam", "basecoverage"),
    ("devteam", "basecoverage"),
    ("devteam", "best_regression_subsets"),
    ("devteam", "bowtie2"),
    ("devteam", "bowtie_color_wrappers"),
    ("devteam", "bowtie_wrappers"),
    ("devteam", "bwa"),
    ("devteam", "canonical_correlation_analysis"),
    ("devteam", "categorize_elements_satisfying_criteria"),
    ("devteam", "ccat"),
    ("devteam", "clustalw"),
    ("devteam", "cluster"),
    ("devteam", "cluster"),
    ("devteam", "column_maker"),
    ("devteam", "column_maker"),
    ("devteam", "complement"),
    ("devteam", "complement"),
    ("devteam", "compute_motif_frequencies_for_all_motifs"),
    ("devteam", "compute_motifs_frequency"),
    ("devteam", "concat"),
    ("devteam", "correlation"),
    ("devteam", "count_gff_features"),
    ("devteam", "coverage"),
    ("devteam", "ctd_batch"),
    ("devteam", "cuffcompare"),
    ("devteam", "cuffcompare"),
    ("devteam", "cuffdiff"),
    ("devteam", "cufflinks"),
    ("devteam", "cufflinks"),
    ("devteam", "cuffmerge"),
    ("devteam", "cuffnorm"),
    ("devteam", "cuffquant"),
    ("devteam", "cummerbund"),
    ("devteam", "cummerbund_to_tabular"),
    ("devteam", "delete_overlapping_indels"),
    ("devteam", "dgidb_annotator"),
    ("devteam", "dgidb_annotator"),
    ("devteam", "divide_pg_snp"),
    ("devteam", "dna_filtering"),
    ("devteam", "draw_stacked_barplots"),
    ("devteam", "dwt_var_perfeature"),
    ("devteam", "emboss_5"),
    ("devteam", "express"),
    ("devteam", "fasta_compute_length"),
    ("devteam", "fasta_concatenate_by_species"),
    ("devteam", "fasta_filter_by_length"),
    ("devteam", "fasta_formatter"),
    ("devteam", "fasta_nucleotide_changer"),
    ("devteam", "fasta_to_tabular"),
    ("devteam", "fastq_combiner"),
    ("devteam", "fastq_filter"),
    ("devteam", "fastq_groomer"),
    ("devteam", "fastq_manipulation"),
    ("devteam", "fastq_masker_by_quality"),
    ("devteam", "fastq_paired_end_deinterlacer"),
    ("devteam", "fastq_paired_end_interlacer"),
    ("devteam", "fastq_paired_end_interlacer"),
    ("devteam", "fastq_paired_end_joiner"),
    ("devteam", "fastq_paired_end_joiner"),
    ("devteam", "fastq_paired_end_splitter"),
    ("devteam", "fastq_quality_boxplot"),
    ("devteam", "fastq_quality_converter"),
    ("devteam", "fastq_quality_filter"),
    ("devteam", "fastq_stats"),
    ("devteam", "fastq_to_fasta"),
    ("devteam", "fastq_to_tabular"),
    ("devteam", "fastq_trimmer"),
    ("devteam", "fastq_trimmer_by_quality"),
    ("devteam", "fastqc"),
    ("devteam", "fastqtofasta"),
    ("devteam", "fastx_artifacts_filter"),
    ("devteam", "fastx_barcode_splitter"),
    ("devteam", "fastx_clipper"),
    ("devteam", "fastx_collapser"),
    ("devteam", "fastx_nucleotides_distribution"),
    ("devteam", "fastx_quality_statistics"),
    ("devteam", "fastx_renamer"),
    ("devteam", "fastx_reverse_complement"),
    ("devteam", "fastx_trimmer"),
    ("devteam", "featurecounter"),
    ("devteam", "filter_transcripts_via_tracking"),
    ("devteam", "find_diag_hits"),
    ("devteam", "flanking_features"),
    ("devteam", "freebayes"),
    ("devteam", "generate_pc_lda_matrix"),
    ("devteam", "get_flanks"),
    ("devteam", "gffread"),
    ("devteam", "gi2taxonomy"),
    ("devteam", "gmaj"),
    ("devteam", "hgv_fundo"),
    ("devteam", "hgv_hilbertvis"),
    ("devteam", "histogram"),
    ("devteam", "indels_3way"),
    ("devteam", "intersect"),
    ("devteam", "join"),
    ("devteam", "kernel_canonical_correlation_analysis"),
    ("devteam", "kernel_principal_component_analysis"),
    ("devteam", "kraken"),
    ("devteam", "kraken2tax"),
    ("devteam", "kraken_filter"),
    ("devteam", "kraken_report"),
    ("devteam", "kraken_translate"),
    ("devteam", "lastz"),
    ("devteam", "lastz_paired_reads"),
    ("devteam", "lca_wrapper"),
    ("devteam", "lda_analysis"),
    ("devteam", "macs"),
    ("devteam", "megablast_wrapper"),
    ("devteam", "megablast_xml_parser"),
    ("devteam", "merge"),
    ("devteam", "merge_cols"),
    ("devteam", "mine"),
    ("devteam", "mutate_snp_codon"),
    ("devteam", "ncbi_blast_plus"),
    ("devteam", "picard"),
    ("devteam", "pileup_interval"),
    ("devteam", "pileup_parser"),
    ("devteam", "plot_from_lda"),
    ("devteam", "poisson2test"),
    ("devteam", "principal_component_analysis"),
    ("devteam", "sam2interval"),
    ("devteam", "sam_bitwise_flag_filter"),
    ("devteam", "sam_merge"),
    ("devteam", "sam_pileup"),
    ("devteam", "sam_to_bam"),
    ("devteam", "samtool_filter2"),
    ("devteam", "samtools_bedcov"),
    ("devteam", "samtools_calmd"),
    ("devteam", "samtools_flagstat"),
    ("devteam", "samtools_idxstats"),
    ("devteam", "samtools_mpileup"),
    ("devteam", "samtools_phase"),
    ("devteam", "samtools_reheader"),
    ("devteam", "samtools_rmdup"),
    ("devteam", "samtools_slice_bam"),
    ("devteam", "samtools_sort"),
    ("devteam", "samtools_split"),
    ("devteam", "samtools_stats"),
    ("devteam", "scatterplot"),
    ("devteam", "short_reads_figure_score"),
    ("devteam", "short_reads_trim_seq"),
    ("devteam", "sicer"),
    ("devteam", "snpfreq"),
    ("devteam", "subtract"),
    ("devteam", "subtract"),
    ("devteam", "subtract_query"),
    ("devteam", "t2ps"),
    ("devteam", "t2t_report"),
    ("devteam", "t_test_two_samples"),
    ("devteam", "tables_arithmetic_operations"),
    ("devteam", "tabular_to_fasta"),
    ("devteam", "tabular_to_fastq"),
    ("devteam", "tophat2"),
    ("devteam", "tophat_fusion_post"),
    ("devteam", "ucsc_custom_track"),
    ("devteam", "varscan_version_2"),
    ("devteam", "vcf2pgsnp"),
    ("devteam", "vcf2tsv"),
    ("devteam", "vcf_filter"),
    ("devteam", "vcfaddinfo"),
    ("devteam", "vcfallelicprimitives"),
    ("devteam", "vcfannotate"),
    ("devteam", "vcfannotategenotypes"),
    ("devteam", "vcfbedintersect"),
    ("devteam", "vcfbreakcreatemulti"),
    ("devteam", "vcfcheck"),
    ("devteam", "vcfcombine"),
    ("devteam", "vcfcommonsamples"),
    ("devteam", "vcfdistance"),
    ("devteam", "vcffilter"),
    ("devteam", "vcffixup"),
    ("devteam", "vcfflatten"),
    ("devteam", "vcfgeno2haplo"),
    ("devteam", "vcfgenotypes"),
    ("devteam", "vcfhethom"),
    ("devteam", "vcfleftalign"),
    ("devteam", "vcfprimers"),
    ("devteam", "vcfrandomsample"),
    ("devteam", "vcfselectsamples"),
    ("devteam", "vcfsort"),
    ("devteam", "vcftools_annotate"),
    ("devteam", "vcftools_compare"),
    ("devteam", "vcftools_isec"),
    ("devteam", "vcftools_merge"),
    ("devteam", "vcftools_slice"),
    ("devteam", "vcftools_subset"),
    ("devteam", "vcfvcfintersect"),
    ("devteam", "weblogo3"),
    ("devteam", "xy_plot"),
    ("galaxyp", "fasta_merge_files_and_filter_unique_sequences"),
    ("nml", "metaspades"),
    ("nml", "spades")
)

for file in glob.glob("*.yaml"):
    print("Processing %s" % file)

    # Load the main tool list containing just the owner/repo name
    with open(file, 'r') as handle:
        unlocked = yaml.load(handle)
    # If a lock file exists, load it from that file
    if os.path.exists(file + '.lock'):
        with open(file + '.lock', 'r') as handle:
            locked = yaml.load(handle)
    else:
        # Otherwise just clone the "unlocked" list.
        locked = copy.deepcopy(unlocked)

    # Extract the name of every tool. This will potentially be outdated if
    # someone has added something to the main file. this is intentional.
    locked_tools = [x['name'] for x in locked['tools']]

    # As here we add any new tools in.
    for tool in unlocked['tools']:
        if tool['name'] not in locked_tools:
            # Add it to the set of locked tools.
            locked['tools'].append(tool)

    # Update any locked tools.
    for tool in locked['tools']:
        # if the tool is trusted, update it.
        if tool['owner'] in TRUSTED_AUTHORS or (tool['owner'], tool['name']) in TRUSTED_REPOSITORIES:
            # get CR
            try:
                revs = ts.repositories.get_ordered_installable_revisions(tool['name'], tool['owner'])
            except Exception as e:
                print(e)
                continue
            # Get latest rev, if not already added, add it.
            if 'changeset_revision' in tool:
                if revs[0] not in tool['changeset_revision']:
                    tool['changeset_revision'].append(revs[0])
                    print("  Found newer revision of %s/%s (%s)" % (tool['owner'], tool['name'], revs[0]))
            else:
                tool['changeset_revision'] = [revs[0]]
                print("  Found newer revision of %s/%s (%s)" % (tool['owner'], tool['name'], revs[0]))

    with open(file + '.lock', 'w') as handle:
        yaml.dump(locked, handle, default_flow_style=False)
