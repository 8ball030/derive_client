from dataclasses import dataclass
from .module_data import ModuleData
from decimal import Decimal
from web3 import Web3
from eth_abi.abi import encode


@dataclass
class DepositModuleData(ModuleData):
    amount: Decimal
    asset: str
    manager: str

    # metadata
    decimals: int

    def to_abi_encoded(self):
        return encode(
            ["uint", "address", "address"],
            [
                int(self.amount * Decimal(10) ** self.decimals),
                Web3.to_checksum_address(self.asset),
                Web3.to_checksum_address(self.manager),
            ],
        )


@dataclass
class SubaccountDepositModuleData:
    amount: Decimal
    asset: str
    subaccount_id: int


    # metadata
    decimals: int

    def to_abi_encoded(self):
        return encode(
            ["uint", "address", "uint"],
            [
                int(self.amount * Decimal(10) ** self.decimals),
                Web3.to_checksum_address(self.asset),
                self.subaccount_id,
            ],
        )