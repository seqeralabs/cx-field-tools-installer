from datetime import UTC, datetime
import json
import logging
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile


base_import_dir = Path(__file__).resolve().parents[2]
if base_import_dir not in sys.path:
    sys.path.append(str(base_import_dir))

from installer.utils.logger import logger  # noqa: E402  (sys.path manipulation above)


## ------------------------------------------------------------------------------------
## Convert HCL (terraform.tfvars, *.tf) to JSON via `tmccombs/hcl2json`.
##
## History:
##   - May 16, 2025: replaced the bespoke parser with a Docker-based call to the vendored
##     `tmccombs/hcl2json` image (origin: https://github.com/tmccombs/hcl2json).
##   - Phases 1+2 of #352: the vendored container is now treated as a delivery vehicle for the
##     Go binary. The Makefile `extract_hcl2json` recipe pulls the binary out once and
##     places it at HCL2JSON_BIN; this module execs the binary directly on supported
##     platforms (linux/amd64 and linux/arm64), eliminating ~1-2s of per-call Docker startup
##     overhead and letting `tests/unit/` run inside sandboxes that block runtime Docker.
##     Hosts that aren't covered yet (Darwin until Phase 3) keep the per-call `docker run`
##     fallback. Phase 2 activation requires the vendored image to be a multi-arch manifest
##     (mirror of upstream `tmccombs/hcl2json` via `docker buildx imagetools create`); the
##     pinned digest is marked with a `TODO(#352-phase2)` comment until that republish lands.
## ------------------------------------------------------------------------------------

HCL2JSON_BIN = "/tmp/cx-installer/hcl2json"  # noqa: S108  (matches Makefile HCL2JSON_BIN; project-namespaced so bwrap jails can mount it)


def _is_supported_extraction_platform() -> bool:
    """Hosts covered by the extracted-binary path (Phases 1+2 of #352: linux/amd64 and linux/arm64).

    `aarch64` is the canonical Linux ARM64 kernel name (what `uname -m` returns); `arm64` is
    accepted defensively in case a container runtime reports the Darwin string on Linux.
    """
    return platform.system() == "Linux" and platform.machine() in {"x86_64", "aarch64", "arm64"}


def _can_use_binary() -> bool:
    """True iff the extracted hcl2json binary is present, executable, and runnable on this host."""
    return _is_supported_extraction_platform() and Path(HCL2JSON_BIN).is_file() and os.access(HCL2JSON_BIN, os.X_OK)


def _docker_run_hcl2json(path: str) -> dict:
    """Fall-back path: parse an HCL file by spawning the vendored container per call.

    Kept for platforms not yet covered by the extracted-binary path (Darwin until Phase 3).
    Per-call cost is ~1-2s of Docker startup overhead.
    """
    # Single local file mounted as read-only, non-root user, disabled network capabilities, and
    # use of immutable container hash fingerprint over mutable tag. The hardcoded `--platform`
    # flag was dropped in Phase 2 so the daemon can pick the matching arch from the multi-arch
    # manifest; forcing amd64 would silently run under emulation on arm64 hosts.
    cmd = [
        "docker",
        "run",
        "-i",
        "--rm",
        "-v",
        f"{path}:/tmp/input.hcl:ro",
        "--user",
        "1000:1000",
        "--network",
        "none",
        # TODO(#352-phase2): replace with the multi-arch manifest digest produced by
        # `docker buildx imagetools create` once the vendored image is republished.
        "ghcr.io/seqeralabs/cx-field-tools-installer/hcl2json@sha256:48af2029d19d824ba1bd1662c008e691c04d5adcb055464e07b2dc04980dcbf5",
        "/tmp/input.hcl",  # noqa: S108  (container-internal mount target, not a host path)
    ]

    result = subprocess.run(cmd, check=False, capture_output=True, text=True)  # noqa: S603  (cmd is a hardcoded list with vendored container hash)

    if result.returncode != 0:
        raise RuntimeError(f"Docker command failed:\nSTDERR: {result.stderr.strip()}")

    payload = result.stdout.strip()

    # Optional debug dump of raw hcl2json output.
    if logging.getLevelName(logger.getEffectiveLevel()) == "DEBUG":
        timestamp = datetime.now(tz=UTC).strftime("%Y_%b%d_%I-%M%p")
        with tempfile.NamedTemporaryFile(
            delete=False,
            prefix=f"hcl2json_{timestamp}_",
            suffix=".json",
            mode="w+",
            dir="/tmp",
        ) as temp_output:
            temp_output.write(payload)

    try:
        return json.loads(payload)
    except json.JSONDecodeError as e:
        raise RuntimeError("Failed to decode Docker output as JSON.") from e


def hcl_to_json(path: str) -> dict:
    """Parse an HCL file (`*.tfvars`, `*.tf`) to a Python dict via `tmccombs/hcl2json`.

    Dispatch:
      - Supported platform + binary present → exec the extracted binary (~10-50ms per call).
      - Supported platform + binary missing → fail fast with instructions to run the Makefile
        recipe. Sandboxed environments must extract the binary before entering the sandbox.
      - Unsupported platform (Darwin until Phase 3) → fall back to per-call `docker run`.
    """
    if _can_use_binary():
        result = subprocess.run(  # noqa: S603  (cmd[0] is the vendored extracted binary path)
            [HCL2JSON_BIN, path],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)

    if _is_supported_extraction_platform():
        sys.stderr.write(
            f"Error: {HCL2JSON_BIN} not found.\n"
            f"Run `make extract_hcl2json` (or any `make run_tests_*` / `make verify`) "
            f"to prepare the binary before invoking pytest directly.\n",
        )
        sys.exit(1)

    return _docker_run_hcl2json(path)


def get_tfvars_as_json(tfvars_path=None):
    """Convert a `terraform.tfvars` file to a Python dict via hcl2json.

    If `tfvars_path` is None, defaults to `<cwd>/terraform.tfvars` (the production path).
    Tests can pass an explicit absolute path (e.g. to `templates/TEMPLATE_terraform.tfvars`).
    """
    if tfvars_path is None:
        tfvars_path = os.path.abspath("terraform.tfvars")

    if not os.path.exists(tfvars_path):
        raise FileNotFoundError(f"terraform.tfvars file not found in path: {tfvars_path}.")

    return hcl_to_json(tfvars_path)
