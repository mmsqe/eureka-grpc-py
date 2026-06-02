# ibc-eureka-py

Python gRPC stubs for the [`ibc-eureka-relayer`](https://github.com/cosmos/solidity-ibc-eureka/tree/d1fdeda/programs/relayer)
proof API and the attestor service it talks to.

```python
from ibc_eureka.ibc_attestor import ibc_attestor_pb2, ibc_attestor_pb2_grpc
from ibc_eureka.relayer import relayer_pb2, relayer_pb2_grpc
```

Regenerate after bumping the protos under `protos/eureka/`:

```sh
uv run --group dev ./scripts/regen-stubs.sh
```
