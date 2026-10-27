"""Locate, install and run the external tools the pipeline shells out to.

The CCG derivations come from the C&C parser. ccg2lambda is only used as an
intermediary: it supplies the tokenizer sed script and the C&C -> transccg XML
converter, and its ``en/install_candc.sh`` knows how to fetch C&C.

Resolution order for each tool (first hit wins):
    explicit argument  >  environment variable  >  ``external/`` dir  >  legacy default
An *explicit* argument that does not point at a valid install is an error; it is
never silently replaced by another location.

If a tool is not found and was not given explicitly, run_pipeline installs it
automatically (first run only). Run ``python parse_sentences.py`` to install
everything up front.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

CCG2LAMBDA_URL = "https://github.com/mynlp/ccg2lambda.git"
# Google Drive id of the C&C models, taken from ccg2lambda's en/install_candc.sh.
CANDC_MODELS_ID = "1LR6h3rX7a4Dq7fV_bc2mEmeYxteSyenH"

# Needed by ccg2lambda's en/candc2transccg.py, which we run with *this* interpreter.
PYTHON_DEPS = ["lxml", "simplejson", "pyyaml", "gdown"]

PathLike = Union[str, "os.PathLike[str]"]


class ToolNotFoundError(RuntimeError):
    """ccg2lambda or C&C could not be located."""


class InstallError(RuntimeError):
    """Installing ccg2lambda or C&C failed."""


@dataclass(frozen=True)
class ToolPaths:
    ccg2lambda: Path
    candc: Path

# All CCG derivation files (tokenised text, C&C XML, transccg XML) go here by default.
DEFAULT_CCG_DIR = Path("ccg_output")


@dataclass(frozen=True)
class CCGOutputs:
    tok: Path           # tokenised sentences
    candc_xml: Path     # raw C&C XML
    transccg_xml: Path  # ccg2lambda transccg XML


def ccg_output_paths(output_dir: Optional[PathLike] = None) -> CCGOutputs:
    """Single source of truth for where the CCG files live."""
    out = Path(output_dir) if output_dir else DEFAULT_CCG_DIR
    return CCGOutputs(
        tok=out / "sentences.tok",
        candc_xml=out / "sentences.candc.xml",
        transccg_xml=out / "sentences.xml",
    )
# ----------------------------------------------------------------------------
# Locations
# ----------------------------------------------------------------------------

def default_external_dir() -> Path:
    """Where auto-installed tools go: $SEMPARSBOXER_EXTERNAL, else ./external next to this file."""
    env = os.environ.get("SEMPARSBOXER_EXTERNAL")
    if env:
        return Path(env).expanduser()
    return Path(__file__).resolve().parent / "external"


def is_ccg2lambda(path: Path) -> bool:
    return (path / "en" / "candc2transccg.py").is_file() and (path / "en" / "tokenizer.sed").is_file()


def is_candc(path: Path) -> bool:
    return (path / "bin" / "candc").is_file() and (path / "models").is_dir()


# ----------------------------------------------------------------------------
# Resolution
# ----------------------------------------------------------------------------

def resolve_ccg2lambda(explicit: Optional[PathLike] = None) -> Path:
    if explicit:
        p = Path(explicit).expanduser()
        if not is_ccg2lambda(p):
            raise ToolNotFoundError(
                f"{p} does not look like a ccg2lambda checkout "
                "(expected en/candc2transccg.py and en/tokenizer.sed)."
            )
        return p

    candidates = []
    if os.environ.get("CCG2LAMBDA_PATH"):
        candidates.append(Path(os.environ["CCG2LAMBDA_PATH"]).expanduser())
    candidates.append(default_external_dir() / "ccg2lambda")
    candidates.append(Path.home() / "ccg2lambda")  # legacy default

    for c in candidates:
        if is_ccg2lambda(c):
            return c
    raise ToolNotFoundError(
        "ccg2lambda not found. Looked in: " + ", ".join(str(c) for c in candidates)
    )


def resolve_candc(explicit: Optional[PathLike] = None,
                  ccg2lambda: Optional[PathLike] = None) -> Path:
    if explicit:
        p = Path(explicit).expanduser()
        if not is_candc(p):
            raise ToolNotFoundError(
                f"{p} does not look like a C&C install (expected bin/candc and models/)."
            )
        return p

    candidates = []
    if os.environ.get("CANDC_PATH"):
        candidates.append(Path(os.environ["CANDC_PATH"]).expanduser())

    if ccg2lambda:
        c2l = Path(ccg2lambda)
        # install_candc.sh writes en/parser_location.txt, while the ccg2lambda README (and
        # some of its scripts) mention en/candc_location.txt: accept both, one path per line.
        # Stale entries (e.g. left behind by a failed download) are ignored by is_candc below.
        for name in ("parser_location.txt", "candc_location.txt"):
            loc = c2l / "en" / name
            if loc.is_file():
                candidates.extend(Path(line.strip()).expanduser()
                                  for line in loc.read_text().splitlines() if line.strip())
        candidates.extend(sorted(c2l.glob("candc*")))

    for c in candidates:
        if is_candc(c):
            return c
    raise ToolNotFoundError(
        "C&C not found. "
        + ("Looked in: " + ", ".join(str(c) for c in candidates) if candidates else "")
    )


def resolve_tools(ccg2lambda: Optional[PathLike] = None,
                  candc: Optional[PathLike] = None) -> ToolPaths:
    c2l = resolve_ccg2lambda(ccg2lambda)
    return ToolPaths(ccg2lambda=c2l, candc=resolve_candc(candc, c2l))


# ----------------------------------------------------------------------------
# Installation
# ----------------------------------------------------------------------------

def _run(cmd, cwd: Optional[Path] = None) -> None:
    print("  $ " + " ".join(str(c) for c in cmd), file=sys.stderr)
    try:
        subprocess.run([str(c) for c in cmd], cwd=cwd, check=True)
    except FileNotFoundError as e:
        raise InstallError(f"Command not found: {cmd[0]}") from e
    except subprocess.CalledProcessError as e:
        raise InstallError(f"Command failed (exit {e.returncode}): {' '.join(str(c) for c in cmd)}") from e


def check_prerequisites() -> None:
    missing = [t for t in ("git", "bash", "sed") if shutil.which(t) is None]
    if shutil.which("wget") is None and shutil.which("curl") is None:
        missing.append("wget or curl")
    if missing:
        raise InstallError("Missing system tools: " + ", ".join(missing))


def install_ccg2lambda(external_dir: Optional[PathLike] = None) -> Path:
    """Clone ccg2lambda into ``<external_dir>/ccg2lambda`` (no-op if already there)."""
    base = Path(external_dir).expanduser() if external_dir else default_external_dir()
    target = base / "ccg2lambda"
    if is_ccg2lambda(target):
        print(f"ccg2lambda already present at {target}", file=sys.stderr)
        return target
    if target.exists() and any(target.iterdir()):
        raise InstallError(
            f"{target} exists but is not a valid ccg2lambda checkout; remove it and retry."
        )
    base.mkdir(parents=True, exist_ok=True)
    print("Cloning ccg2lambda...", file=sys.stderr)
    _run(["git", "clone", "--depth", "1", CCG2LAMBDA_URL, target])
    if not is_ccg2lambda(target):
        raise InstallError(f"Cloned {CCG2LAMBDA_URL} but {target} is missing expected files.")
    return target


def download_models(candc_dir: PathLike) -> None:
    """Fetch and unpack the C&C models into ``<candc_dir>/models``.

    ccg2lambda's script uses a curl cookie trick for Google Drive's large-file
    confirmation page, which no longer works (it saves the HTML page instead of the
    tarball). ``gdown`` handles that confirmation step.
    """
    import tarfile

    d = Path(candc_dir)
    archive = d / "models-1.02.tgz"
    print("Downloading C&C models with gdown...", file=sys.stderr)
    _run([sys.executable, "-m", "gdown", CANDC_MODELS_ID, "-O", archive])
    if not archive.is_file() or archive.read_bytes()[:2] != b"\x1f\x8b":
        archive.unlink(missing_ok=True)
        raise InstallError(
            "The downloaded models file is not a gzip archive (Google Drive probably served "
            "a quota/permission page). Download models-1.02.tgz manually, extract it inside "
            f"{d} so that {d / 'models'} exists, and re-run."
        )
    with tarfile.open(archive) as tar:
        tar.extractall(d, filter="data") if sys.version_info >= (3, 12) else tar.extractall(d)
    archive.unlink()
    if not (d / "models").is_dir():
        raise InstallError(f"Extracted the models archive but {d / 'models'} does not exist.")


def install_candc(ccg2lambda: PathLike) -> Path:
    """Install C&C using ccg2lambda's own script (no-op if already resolvable)."""
    c2l = Path(ccg2lambda)
    try:
        existing = resolve_candc(None, c2l)
        print(f"C&C already present at {existing}", file=sys.stderr)
        return existing
    except ToolNotFoundError:
        pass

    candc_dir = c2l / "candc-1.00"
    if not (candc_dir / "bin" / "candc").is_file():
        if candc_dir.exists():
            # install_candc.sh skips the download entirely when this directory exists, so a
            # broken earlier attempt would never be repaired by re-running it.
            raise InstallError(
                f"{candc_dir} exists but contains no C&C binary.\n"
                f"Remove it and retry:  rm -rf {candc_dir}"
            )
        print("Installing C&C (en/install_candc.sh)...", file=sys.stderr)
        # The script exits 0 and writes en/parser_location.txt even if its downloads fail,
        # so success is judged by validating the result, not by the exit code.
        _run(["bash", "en/install_candc.sh"], cwd=c2l)

    # The parser tarball downloads fine but the models usually do not: repair that step.
    if (candc_dir / "bin" / "candc").is_file() and not (candc_dir / "models").is_dir():
        download_models(candc_dir)

    try:
        return resolve_candc(None, c2l)
    except ToolNotFoundError as e:
        raise InstallError(
            "en/install_candc.sh ran but produced no usable C&C install.\n"
            "Manual fallback: obtain C&C 1.00 and its models (see "
            "https://sites.google.com/site/stephenclark609/resources/c-c_parser or\n"
            "https://github.com/valeriobasile/learningbyreading#installation-of-the-cc-tools-and-boxer),\n"
            "so that <dir>/bin/candc and <dir>/models/ exist, then either\n"
            f"  echo <dir> > {c2l / 'en' / 'parser_location.txt'}\n"
            "or set CANDC_PATH=<dir> (or pass --candc <dir>), and re-run."
        ) from e


def install_python_deps() -> None:
    _run([sys.executable, "-m", "pip", "install", *PYTHON_DEPS])


def ensure_tools(ccg2lambda: Optional[PathLike] = None,
                 candc: Optional[PathLike] = None,
                 auto_install: bool = True) -> ToolPaths:
    """Resolve both tools, installing whichever is missing (unless given explicitly).

    An explicit path that is invalid raises ToolNotFoundError and is never replaced.
    Already-installed tools are found by the resolvers, so nothing is downloaded twice.
    """
    installed_something = False

    if ccg2lambda:
        c2l = resolve_ccg2lambda(ccg2lambda)
    else:
        try:
            c2l = resolve_ccg2lambda()
        except ToolNotFoundError:
            if not auto_install:
                raise
            print("ccg2lambda not found: installing automatically...", file=sys.stderr)
            check_prerequisites()
            c2l = install_ccg2lambda()
            installed_something = True

    if candc:
        cc = resolve_candc(candc, c2l)
    else:
        try:
            cc = resolve_candc(None, c2l)
        except ToolNotFoundError:
            if not auto_install:
                raise
            print("C&C not found: installing automatically...", file=sys.stderr)
            check_prerequisites()
            cc = install_candc(c2l)
            installed_something = True

    if installed_something:
        install_python_deps()  # only on first-time installs
    return ToolPaths(ccg2lambda=c2l, candc=cc)


# ----------------------------------------------------------------------------
# Backwards-compatible helpers (same names as before)
# ----------------------------------------------------------------------------

def get_ccg2lambda_path(path: str = None) -> str:
    return str(ensure_tools(ccg2lambda=path, candc=None).ccg2lambda) if path is None \
        else str(resolve_ccg2lambda(path))


def get_candc_path(path: str = None) -> str:
    return str(ensure_tools(candc=path).candc)


# ----------------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------------

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
    models = str(Path(root) / "models")
    with open(output_path, "w") as outfile:
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
    with open(output_path, "w") as outfile:
        result = subprocess.run(
            [sys.executable, script, input_path],  # same interpreter the deps were installed into
            stdout=outfile,
            stderr=subprocess.PIPE
        )
    if result.returncode != 0:
        raise RuntimeError(f"candc2transccg failed: {result.stderr.decode()}")

def run_pipeline(
    sentences_path: str,
    output_dir: Optional[PathLike] = None,
    ccg2lambda_path: str = None,
    candc_path: str = None,
    verbose: bool = True,
):
    # resolve (and, on the very first run, install) once per run
    tools = ensure_tools(ccg2lambda_path, candc_path)
    ccg2lambda_path, candc_path = str(tools.ccg2lambda), str(tools.candc)

    outputs = ccg_output_paths(output_dir)
    outputs.tok.parent.mkdir(parents=True, exist_ok=True)   # creates ccg_output/ if missing

    if verbose: print(f"CCG output directory: {outputs.tok.parent}")

    if verbose: print("Tokenising...")
    tokenize(sentences_path, str(outputs.tok), ccg2lambda_path)

    if verbose: print("Parsing with C&C...")
    parse_candc(str(outputs.tok), str(outputs.candc_xml), candc_path)

    if verbose: print("Converting to XML...")
    candc_to_transccg(str(outputs.candc_xml), str(outputs.transccg_xml), ccg2lambda_path)

    if verbose: print(f"Output: {outputs.transccg_xml}")
    return str(outputs.transccg_xml)


# ----------------------------------------------------------------------------
# Optional: explicit one-off setup + smoke test
# ----------------------------------------------------------------------------

def smoke_test(tools: ToolPaths) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sent = Path(tmp) / "smoke.txt"
        sent.write_text("A woman is ordering tea.\n")
        run_pipeline(str(sent), tmp, str(tools.ccg2lambda), str(tools.candc), verbose=False)
        out = ccg_output_paths(tmp)
        for label, path in (("C&C XML", out.candc_xml), ("transccg XML", out.transccg_xml)):
            if "<ccg" not in path.read_text(errors="replace"):
                raise InstallError(f"Smoke test failed: {label} output has no <ccg> derivation.")
def setup(external_dir: Optional[PathLike] = None,
          *, python_deps: bool = True, run_smoke_test: bool = True) -> ToolPaths:
    """Install everything needed to run the pipeline and return the resolved paths."""
    check_prerequisites()
    if python_deps:
        install_python_deps()
    c2l = install_ccg2lambda(external_dir)
    candc = install_candc(c2l)
    tools = ToolPaths(ccg2lambda=c2l, candc=candc)
    if run_smoke_test:
        print("Running smoke test...", file=sys.stderr)
        smoke_test(tools)
    return tools


if __name__ == "__main__":
    t = setup()
    print(f"ccg2lambda: {t.ccg2lambda}\nC&C:        {t.candc}")