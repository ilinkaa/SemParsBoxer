from pathlib import Path
import subprocess 
import shutil

import os

#AI code
# Pipeline calling the CandC tools to obtain the CCG parse in XML format

def get_candc_path(path: str = None) -> str:
    if path:
        return path
    if "CANDC_PATH" in os.environ:
        return os.environ["CANDC_PATH"]
    raise EnvironmentError(
        "C&C not found. Set CANDC_PATH environment variable "
        "(e.g. export CANDC_PATH=/path/to/candc-1.00) "
        "or pass path explicitly."
    )

def get_ccg2lambda_path(path: str = None) -> str:
    # priority: explicit arg > env var > default
    if path:
        return path
    if "CCG2LAMBDA_PATH" in os.environ:
        return os.environ["CCG2LAMBDA_PATH"]
    default = Path.home() / "ccg2lambda"
    if default.exists():
        return str(default)
    raise EnvironmentError(
        "ccg2lambda not found. Set CCG2LAMBDA_PATH environment variable "
        "or pass path explicitly."
    )

def tokenize(input_path: str, output_path: str, ccg2lambda_path: str = None):
    root = get_ccg2lambda_path(ccg2lambda_path)
    sed_script = str(Path(root) / "en/tokenizer.sed")
    
    with open(input_path) as infile, open(output_path, "w") as outfile:
        result = subprocess.run(
            ["sed", "-f", sed_script],
            stdin=infile,
            stdout=outfile,
            stderr=subprocess.PIPE
        )
    if result.returncode != 0:
        raise RuntimeError(f"Tokenization failed: {result.stderr.decode()}")

def parse_candc(input_path: str, output_path: str, candc_path: str = None):
    """Run C&C parser to produce XML output."""
    root = get_candc_path(candc_path)
    binary = str(Path(root) / "bin/candc")
    models  = str(Path(root) / "models")
    
    with open(input_path) as infile, open(output_path, "w") as outfile:
        result = subprocess.run(
            [binary, "--models", models, "--candc-printer", "xml", "--input", input_path],
            stdout=outfile,
            stderr=subprocess.PIPE
        )
    if result.returncode != 0:
        raise RuntimeError(f"C&C parsing failed: {result.stderr.decode()}")


def candc_to_transccg(input_path: str, output_path: str, ccg2lambda_path: str = None):
    """Convert C&C XML to transccg format."""
    root = get_ccg2lambda_path(ccg2lambda_path)
    script = str(Path(root) / "en/candc2transccg.py")
    
    with open(input_path) as infile, open(output_path, "w") as outfile:
        result = subprocess.run(
            ["python", script, input_path],
            stdout=outfile,
            stderr=subprocess.PIPE
        )
      
    if result.returncode != 0:
        raise RuntimeError(f"candc2transccg failed: {result.stderr.decode()}")
    

from pathlib import Path

def run_pipeline(
    sentences_path: str,
    output_dir: str = ".",
    ccg2lambda_path: str = None,
    candc_path: str = None,
):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    tok_path    = str(out / "sentences.tok")
    candc_path_ = str(out / "sentences.candc.xml")
    xml_path    = str(out / "sentences.xml")

    print("Tokenising...")
    tokenize(sentences_path, tok_path, ccg2lambda_path)

    print("Parsing with C&C...")
    parse_candc(tok_path, candc_path_, candc_path)

    print("Converting to XML...")
    candc_to_transccg(candc_path_, xml_path, ccg2lambda_path)

    print(f"Output: {xml_path}")
    return xml_path
