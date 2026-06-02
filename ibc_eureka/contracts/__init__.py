"""Compile + deploy the solidity-ibc-eureka contracts (the send-side stack, the
SP1 ICS07-Tendermint client, light clients).

Imports solcx + web3 + eth-* — not pulled by the base stubs install; provide them
yourself. Point ``$EUREKA_REPO_PATH`` at the solidity-ibc-eureka checkout (or run
from a dir whose ``../`` or ``../../`` contains it).
"""
