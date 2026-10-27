import argparse
import xml.etree.ElementTree as ET

from parse_sentences import run_pipeline, ccg_output_paths, DEFAULT_CCG_DIR
from parse_CCG import parse_sent_ccg


def main():
    parser = argparse.ArgumentParser(
        description="Run the CCG pipeline and parse the resulting CCGs."
    )

    parser.add_argument(
        "sentences", nargs="?",
        help="Input text file containing sentences (not needed with --parse-only)."
    )

    parser.add_argument(
        "-o", "--output-dir",
        default=str(DEFAULT_CCG_DIR),
        help=f"Directory for the CCG derivation files (default: {DEFAULT_CCG_DIR}/)."
    )

    parser.add_argument(
        "--parse-only", action="store_true",
        help="Skip tokenising/C&C and parse the derivations already in the output directory."
    )

    parser.add_argument(
        "--ccg2lambda", default=None,
        help="Optional: path to the ccg2lambda installation (otherwise found or installed automatically)."
    )

    parser.add_argument(
        "--candc", default=None,
        help="Optional: path to the C&C parser installation (otherwise found or installed automatically)."
    )

    args = parser.parse_args()

    if not args.parse_only:
        if not args.sentences:
            parser.error("the 'sentences' argument is required unless --parse-only is given")
        run_pipeline(args.sentences, args.output_dir, args.ccg2lambda, args.candc)

    candc_xml = ccg_output_paths(args.output_dir).candc_xml
    if not candc_xml.is_file():
        parser.error(f"{candc_xml} not found; run once without --parse-only first")

    root = ET.parse(candc_xml).getroot()

    for ccg in root.findall("ccg"):
        parse_sent_ccg(ccg)


if __name__ == "__main__":
    main()