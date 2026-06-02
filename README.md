# ibc-eureka-py

Python SDK for [IBC Eureka](https://github.com/cosmos/solidity-ibc-eureka/tree/d1fdeda):
gRPC stubs for the `ibc-eureka-relayer` proof API + attestor service, plus optional
helpers built on them.

- `ibc_eureka.relayer` / `ibc_eureka.ibc_attestor` — generated gRPC stubs.
- `ibc_eureka.relayer.client.RelayerClient` — thin client over the proof API.
- `ibc_eureka.relayer.binary.BinaryRelayer` — relay a source tx and submit the
  returned multicall on an EVM dest, or hand a `TxBody` to a `cosmos_signer`.
- `ibc_eureka.harness` — spawn the relayer + attestor binaries and build configs.
- `ibc_eureka.contracts` — compile + deploy the solidity-ibc-eureka contracts.

The base install is stubs-only (`grpcio` + `protobuf`); the helper modules import
web3/eth-*/solcx, which the consumer provides.

```python
from ibc_eureka.relayer import relayer_pb2, relayer_pb2_grpc
from ibc_eureka.relayer.client import RelayerClient
```

Regenerate after bumping the protos under `protos/eureka/`:

```sh
uv run --group dev ./scripts/regen-stubs.sh
```
