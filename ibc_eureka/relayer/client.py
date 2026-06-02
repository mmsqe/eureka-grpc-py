"""Convenience client over the generated ``RelayerService`` stubs.

Wraps a gRPC channel + ``RelayerServiceStub`` and exposes the proof API's two
RPCs as plain calls returning the relayer's raw response bytes. The caller signs
and submits whatever comes back (EVM calldata or a cosmos ``TxBody``) — that part
is chain- and signer-specific and stays out of this package.
"""

from __future__ import annotations

from collections.abc import Sequence

import grpc

from . import relayer_pb2, relayer_pb2_grpc


class RelayerClient:
    """A channel + ``RelayerServiceStub`` against an ``ibc-eureka-relayer``."""

    def __init__(self, address: str) -> None:
        self._channel = grpc.insecure_channel(address)
        self._stub = relayer_pb2_grpc.RelayerServiceStub(self._channel)

    def close(self) -> None:
        self._channel.close()

    def relay_by_tx(
        self,
        *,
        src_chain: str,
        dst_chain: str,
        src_client_id: str,
        dst_client_id: str,
        source_tx_ids: Sequence[bytes] = (),
        timeout_tx_ids: Sequence[bytes] = (),
    ) -> tuple[bytes, str]:
        """Relay ``source_tx_ids`` (recv/ack) or ``timeout_tx_ids`` (timeout).

        Returns ``(tx, address)``: ``tx`` is the multicall to submit (EVM calldata
        or a cosmos ``TxBody``); ``address`` is the EVM target (``""`` for cosmos
        or when the caller already knows it).
        """
        resp = self._stub.RelayByTx(
            relayer_pb2.RelayByTxRequest(
                src_chain=src_chain,
                dst_chain=dst_chain,
                source_tx_ids=list(source_tx_ids),
                timeout_tx_ids=list(timeout_tx_ids),
                src_client_id=src_client_id,
                dst_client_id=dst_client_id,
            )
        )
        return bytes(resp.tx), resp.address

    def create_client(
        self, *, src_chain: str, dst_chain: str, parameters: dict[str, str]
    ) -> bytes:
        """Create a light client (src→dst). Returns the unsigned ``TxBody`` bytes."""
        resp = self._stub.CreateClient(
            relayer_pb2.CreateClientRequest(
                src_chain=src_chain, dst_chain=dst_chain, parameters=parameters
            )
        )
        return bytes(resp.tx)
