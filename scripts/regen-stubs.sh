#!/usr/bin/env bash
# Regenerate Python gRPC stubs from the vendored protos.
set -euo pipefail

cd "$(dirname "$0")/.."

# Wipe + regenerate so stale stubs from removed protos don't linger.
rm -rf eureka_grpc/ibc_attestor eureka_grpc/relayer

python -m grpc_tools.protoc \
    -I protos/eureka \
    --python_out=eureka_grpc \
    --grpc_python_out=eureka_grpc \
    protos/eureka/relayer/relayer.proto \
    protos/eureka/ibc_attestor/ibc_attestor.proto \
    protos/eureka/ibc_attestor/attestation.proto

# protoc doesn't emit __init__.py — drop empty markers so the dirs are
# importable as packages.
touch eureka_grpc/ibc_attestor/__init__.py eureka_grpc/relayer/__init__.py

# protoc emits absolute imports like ``from ibc_attestor import attestation_pb2``
# (proto ``package`` name → top-level Python module). Rewrite them to
# relative-package imports so consumers can ``from eureka_grpc.ibc_attestor
# import …`` without a sys.path hack. Same effect as protoletariat but with
# no extra dep (and protoletariat caps protobuf at <6 anyway).
for pkg in ibc_attestor relayer; do
    sed -i.bak -E "s/^from ${pkg} import /from . import /" eureka_grpc/${pkg}/*.py
    rm -f eureka_grpc/${pkg}/*.py.bak
done

echo "regenerated $(find eureka_grpc -name '*_pb2*.py' | wc -l | xargs) stubs"
