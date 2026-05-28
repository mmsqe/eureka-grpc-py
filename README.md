# eureka-grpc-py

Python gRPC stubs for the [`ibc-eureka-relayer`](https://github.com/cosmos/solidity-ibc-eureka/tree/d1fdeda/programs/relayer) proof API and the
attestor service it talks to.

```python
import eureka_grpc  # side-effect: puts stubs on sys.path
from ibc_attestor import ibc_attestor_pb2, ibc_attestor_pb2_grpc
from relayer import relayer_pb2, relayer_pb2_grpc
```

Regenerate after bumping the protos under `protos/eureka/`:

```sh
uv run --group dev ./scripts/regen-stubs.sh
```
