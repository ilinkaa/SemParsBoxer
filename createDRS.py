
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

from parse_sentences import run_pipeline
from parse_CCG import parse_sent_ccg


def main():
    parser = argparse.ArgumentParser(
        description="Run the CCG pipeline and parse the resulting CCGs."
    )

    parser.add_argument(
        "sentences",
        help="Input text file containing sentences."
    )

    parser.add_argument(
        "-o", "--output-dir",
        default=".",
        help="Directory for generated files (default: current directory)."
    )

    parser.add_argument(
        "--ccg2lambda",
        required=True,
        help="Path to the ccg2lambda installation."
    )

    parser.add_argument(
        "--candc",
        required=True,
        help="Path to the C&C parser installation."
    )

    args = parser.parse_args()

    xml_path = run_pipeline(
        args.sentences,
        args.output_dir,
        args.ccg2lambda,
        args.candc,
    )

    candc_path = Path(xml_path).with_suffix(".candc.xml")

    root = ET.parse(candc_path).getroot()

    for ccg in root.findall("ccg"):
        parse_sent_ccg(ccg)


if __name__ == "__main__":
    main()