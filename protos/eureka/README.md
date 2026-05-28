# Vendored Eureka protos

Snapshots of the `ibc-eureka-relayer` gRPC service definition and the
attestor service it talks to, pinned at upstream commit `d1fdeda`
(same commit that `nix/eureka-relayer.nix` builds the binary from).

| File | Upstream path | Service |
|---|---|---|
| `relayer/relayer.proto` | `proto/relayer/relayer.proto` | `RelayerService` — `RelayByTx`, `UpdateClient`, `CreateClient`, `Info` |
| `ibc_attestor/ibc_attestor.proto` | `proto/ibc_attestor/ibc_attestor.proto` | `AttestationService` — `StateAttestation`, `PacketAttestation`, `LatestHeight` |
| `ibc_attestor/attestation.proto` | `proto/ibc_attestor/attestation.proto` | `Attestation` message |

To regenerate the Python stubs (for the test orchestrator) run from the
``integration_tests/`` directory::

    python -m grpc_tools.protoc \
        -I protos/eureka \
        --python_out=. --grpc_python_out=. \
        protos/eureka/relayer/relayer.proto \
        protos/eureka/ibc_attestor/ibc_attestor.proto \
        protos/eureka/ibc_attestor/attestation.proto

Bump the pinned commit alongside `nix/eureka-relayer.nix` so the binary
and the generated stubs stay in sync.
