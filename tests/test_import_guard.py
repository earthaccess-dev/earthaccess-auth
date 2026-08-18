"""Importing earthaccess_auth must not import any heavy optional dependency.

Runs in a subprocess so this test is independent of what the surrounding
pytest process has already imported. The deps CAN be installed (they are, in
the workspace env) — the invariant is that importing the core never pulls
them in. CI additionally runs the whole suite in an env where they are not
installed at all.
"""

import json
import subprocess
import sys

FORBIDDEN = {"fsspec", "aiohttp", "obstore", "s3fs", "cmr", "pqdm", "tenacity"}


def test_core_import_pulls_no_heavy_dependencies() -> None:
    code = (
        "import json, sys; import earthaccess_auth; "
        "print(json.dumps(sorted({m.split('.')[0] for m in sys.modules})))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    imported = set(json.loads(out.stdout))
    assert not imported & FORBIDDEN, f"core import leaked: {imported & FORBIDDEN}"
