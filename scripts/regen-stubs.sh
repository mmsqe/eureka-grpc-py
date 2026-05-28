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

echo "regenerated $(find eureka_grpc -name '*_pb2*.py' | wc -l | xargs) stubs"
