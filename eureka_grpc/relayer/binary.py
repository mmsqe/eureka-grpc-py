"""Higher-level orchestrator over :class:`RelayerClient`.

The relayer's proof API returns IBC ``MsgRecvPacket`` / ``MsgAckPacket`` /
``MsgTimeout`` calldata + proofs for a source tx; this submits them on the
destination chain. EVM destinations are submitted directly (web3); Cosmos
destinations are handed to a caller-supplied ``cosmos_signer`` (sign + broadcast a
``TxBody``, return the committed tx) so this stays free of any chain-CLI/keyring.

Imports web3 + eth-* — not pulled by the base stubs install; provide them yourself.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable

from eth_account.signers.base import BaseAccount
from eth_contract.utils import send_transaction
from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3 import AsyncWeb3

from .client import RelayerClient

# Signs + broadcasts a serialized cosmos ``TxBody``, returning the committed tx
# (a dict with ``events`` / ``txhash`` / ``code``).
CosmosSigner = Callable[[bytes], dict]


def _event_attrs(events: list, ev_type: str) -> dict | None:
    """First event of ``ev_type``'s attributes as a ``{key: value}`` dict."""
    for ev in events:
        if ev["type"] == ev_type:
            return {a["key"]: a["value"] for a in ev["attributes"]}
    return None


@dataclass
class _Endpoint:
    """One side of a paired Eureka deployment with the signing key."""

    w3: AsyncWeb3
    router_addr: ChecksumAddress
    client_id: str  # local client id
    chain_id: str  # EVM chain id, hex with 0x prefix
    deployer: BaseAccount


class BinaryRelayer:
    """Calls ``RelayByTx`` from→to and submits the returned multicall
    (``updateClient + recv/ack/timeoutPacket``) on the destination — directly for
    an EVM dest, via a ``cosmos_signer`` for a Cosmos dest. Tx-hash dedup makes
    every relay idempotent."""

    def __init__(
        self,
        src: _Endpoint,
        dst: _Endpoint,
        grpc_address: str,
        *,
        evm_gas_limit: int = 2_000_000,
    ) -> None:
        self.src = src
        self.dst = dst
        self._client = RelayerClient(grpc_address)
        self._relayed: set[bytes] = set()
        self._evm_gas_limit = evm_gas_limit

    def close(self) -> None:
        self._client.close()

    @contextmanager
    def _relay_tx(
        self,
        *,
        label: str,
        tx_hash: bytes,
        timeout: bool,
        src_chain: str,
        dst_chain: str,
        src_client_id: str,
        dst_client_id: str,
    ):
        """Dedup + ``RelayByTx``, yielding the returned ``(tx, address)``. The dedup
        mark is held across the caller's submit and discarded if it raises, so a
        transient failure stays retryable while a success sticks (no double-submit).
        ``timeout`` picks ``timeout_tx_ids`` (non-receipt) vs ``source_tx_ids``."""
        key = b"timeout:" + tx_hash if timeout else tx_hash
        if key in self._relayed:
            raise ValueError(f"{label} {tx_hash.hex()} already relayed")
        self._relayed.add(key)
        ids = {"timeout_tx_ids" if timeout else "source_tx_ids": [tx_hash]}
        try:
            yield self._client.relay_by_tx(
                src_chain=src_chain,
                dst_chain=dst_chain,
                src_client_id=src_client_id,
                dst_client_id=dst_client_id,
                **ids,
            )
        except Exception:
            self._relayed.discard(key)
            raise

    async def _submit_evm(
        self, to_side: _Endpoint, tx: bytes, address: str, label: str
    ) -> dict:
        """Submit a relayer-returned multicall on ``to_side``; on revert, replay as
        ``eth_call`` to surface the reason (receipts drop it)."""
        to = HexBytes(address or to_side.router_addr)
        receipt = await send_transaction(
            to_side.w3,
            to_side.deployer,
            to=to,
            data=tx,
            gas=self._evm_gas_limit,
            check=False,
        )
        if receipt["status"] == 1:
            return dict(receipt)
        call = {"to": to, "data": tx, "from": to_side.deployer.address}
        try:
            await to_side.w3.eth.call(call, block_identifier=receipt["blockNumber"])
        except Exception as exc:
            raise RuntimeError(f"{label} reverted (to={to.to_0x_hex()}): {exc}") from exc
        raise RuntimeError(f"{label} reverted but eth_call passed (to={to.to_0x_hex()})")

    async def relay(
        self, from_side: _Endpoint, to_side: _Endpoint, tx_hash: bytes
    ) -> dict:
        """Relay a source tx EVM→EVM: submit the recv/ack multicall on ``to_side``."""
        with self._relay_tx(
            label="tx",
            tx_hash=tx_hash,
            timeout=False,
            src_chain=from_side.chain_id,
            dst_chain=to_side.chain_id,
            src_client_id=from_side.client_id,
            dst_client_id=to_side.client_id,
        ) as (tx, address):
            return await self._submit_evm(to_side, tx, address, "relayer tx")

    def relay_to_cosmos(
        self,
        *,
        src_chain: str,
        dst_chain: str,
        src_client_id: str,
        dst_client_id: str,
        tx_hash: bytes,
        cosmos_signer: CosmosSigner,
    ) -> dict:
        """Relay an EVM source tx to a Cosmos dest: ``cosmos_signer`` signs +
        broadcasts the returned ``MsgRecvPacket``/``MsgAckPacket`` ``TxBody``."""
        with self._relay_tx(
            label="tx",
            tx_hash=tx_hash,
            timeout=False,
            src_chain=src_chain,
            dst_chain=dst_chain,
            src_client_id=src_client_id,
            dst_client_id=dst_client_id,
        ) as (tx, _):
            return cosmos_signer(tx)

    def relay_timeout_to_cosmos(
        self,
        *,
        src_chain: str,
        dst_chain: str,
        src_client_id: str,
        dst_client_id: str,
        timeout_tx_hash: bytes,
        cosmos_signer: CosmosSigner,
    ) -> dict:
        """Relay a cosmos-source packet timeout: ``cosmos_signer`` signs + broadcasts
        the returned ``MsgTimeout`` to refund the sender (non-receipt proven on EVM)."""
        with self._relay_tx(
            label="timeout",
            tx_hash=timeout_tx_hash,
            timeout=True,
            src_chain=src_chain,
            dst_chain=dst_chain,
            src_client_id=src_client_id,
            dst_client_id=dst_client_id,
        ) as (tx, _):
            return cosmos_signer(tx)

    async def relay_timeout(
        self,
        *,
        src_chain: str,
        dst_chain: str,
        src_client_id: str,
        dst_client_id: str,
        timeout_tx_hash: bytes,
        to_side: _Endpoint,
    ) -> dict:
        """Relay a timeout to an EVM source: submit the non-receipt ``timeoutPacket``
        multicall on ``to_side``, which refunds the escrowed tokens."""
        with self._relay_tx(
            label="timeout",
            tx_hash=timeout_tx_hash,
            timeout=True,
            src_chain=src_chain,
            dst_chain=dst_chain,
            src_client_id=src_client_id,
            dst_client_id=dst_client_id,
        ) as (tx, address):
            return await self._submit_evm(to_side, tx, address, "timeout tx")

    def create_attestations_client(
        self,
        *,
        eth_chain_id: str,
        cosmos_chain_id: str,
        attestor_addresses: list[str],
        height: int,
        timestamp: int,
        cosmos_signer: CosmosSigner,
        min_required_sigs: int = 1,
    ) -> str:
        """Create the ibc-go ``attestations`` client tracking the EVM chain via
        ``CreateClient`` (src=eth, dst=cosmos); ``cosmos_signer`` signs + broadcasts
        the returned ``TxBody``. Returns the new client id."""
        tx = self._client.create_client(
            src_chain=eth_chain_id,
            dst_chain=cosmos_chain_id,
            parameters={
                "attestor_addresses": ",".join(attestor_addresses),
                "min_required_sigs": str(min_required_sigs),
                "height": str(height),
                "timestamp": str(timestamp),
            },
        )
        committed = cosmos_signer(tx)
        attrs = _event_attrs(committed.get("events", []), "create_client")
        client_id = (attrs or {}).get("client_id")
        assert client_id, f"no client_id in events: {committed.get('events')}"
        return client_id
