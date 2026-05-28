"""Generated gRPC stubs from upstream solidity-ibc-eureka protos.

Side effect on import: prepends this directory to ``sys.path`` so the
stubs' intra-package imports (``from ibc_attestor import attestation_pb2``,
``from relayer import relayer_pb2``) resolve. Without this each consumer
would need to manipulate sys.path itself.

See ``protos/eureka/README.md`` for regen instructions.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PKG_DIR = str(Path(__file__).parent)
if _PKG_DIR not in sys.path:
    sys.path.insert(0, _PKG_DIR)
