"""
Constants for Lyra.
"""

from pathlib import Path

from derive_client.data_types import Environment, UnderlyingCurrency
from pydantic import BaseModel


class ContractAddresses(BaseModel):
    ETH_PERP_ADDRESS: str
    BTC_PERP_ADDRESS: str
    ETH_OPTION_ADDRESS: str
    BTC_OPTION_ADDRESS: str
    TRADE_MODULE_ADDRESS: str
    STANDARD_RISK_MANAGER_ADDRESS: str
    BTC_PORTFOLIO_RISK_MANAGER_ADDRESS: str
    ETH_PORTFOLIO_RISK_MANAGER_ADDRESS: str
    CASH_ASSET: str
    USDC_ASSET: str
    DEPOSIT_MODULE_ADDRESS: str
    WITHDRAWAL_MODULE_ADDRESS: str
    TRANSFER_MODULE_ADDRESS: str

    def __getitem__(self, key):
        return getattr(self, key)


class EnvConfig(BaseModel):
    base_url: str
    ws_address: str
    action_typehash: str
    domain_separator: str
    contracts: ContractAddresses


REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
ABI_DATA_DIR = DATA_DIR / "abi"

PUBLIC_HEADERS = {"accept": "application/json", "content-type": "application/json"}

TEST_PRIVATE_KEY = "0xc14f53ee466dd3fc5fa356897ab276acbef4f020486ec253a23b0d1c3f89d4f4"
DEFAULT_SPOT_QUOTE_TOKEN = "USDC"

CONFIGS: dict[Environment, EnvConfig] = {
    Environment.TEST: EnvConfig(
        base_url="https://api-demo.lyra.finance",
        ws_address="wss://api-demo.lyra.finance/ws",
        action_typehash="0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17",
        domain_separator="0x9bcf4dc06df5d8bf23af818d5716491b995020f377d3b7b64c29ed14e3dd1105",
        contracts=ContractAddresses(
            ETH_PERP_ADDRESS="0x010e26422790C6Cb3872330980FAa7628FD20294",
            BTC_PERP_ADDRESS="0xAFB6Bb95cd70D5367e2C39e9dbEb422B9815339D",
            ETH_OPTION_ADDRESS="0xBcB494059969DAaB460E0B5d4f5c2366aab79aa1",
            BTC_OPTION_ADDRESS="0xAeB81cbe6b19CeEB0dBE0d230CFFE35Bb40a13a7",
            TRADE_MODULE_ADDRESS="0x87F2863866D85E3192a35A73b388BD625D83f2be",
            STANDARD_RISK_MANAGER_ADDRESS="0x28bE681F7bEa6f465cbcA1D25A2125fe7533391C",
            BTC_PORTFOLIO_RISK_MANAGER_ADDRESS="0xbaC0328cd4Af53d52F9266Cdbd5bf46720320A20",
            ETH_PORTFOLIO_RISK_MANAGER_ADDRESS="0xDF448056d7bf3f9Ca13d713114e17f1B7470DeBF",
            CASH_ASSET="0x6caf294DaC985ff653d5aE75b4FF8E0A66025928",
            USDC_ASSET="0xe80F2a02398BBf1ab2C9cc52caD1978159c215BD",
            DEPOSIT_MODULE_ADDRESS="0x43223Db33AdA0575D2E100829543f8B04A37a1ec",
            WITHDRAWAL_MODULE_ADDRESS="0xe850641C5207dc5E9423fB15f89ae6031A05fd92",
            TRANSFER_MODULE_ADDRESS="0x0CFC1a4a90741aB242cAfaCD798b409E12e68926",
        ),
    ),
    Environment.PROD: EnvConfig(
        base_url="https://api.lyra.finance",
        ws_address="wss://api.lyra.finance/ws",
        action_typehash="0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17",
        domain_separator="0xd96e5f90797da7ec8dc4e276260c7f3f87fedf68775fbe1ef116e996fc60441b",
        contracts=ContractAddresses(
            ETH_PERP_ADDRESS="0xAf65752C4643E25C02F693f9D4FE19cF23a095E3",
            BTC_PERP_ADDRESS="0xDBa83C0C654DB1cd914FA2710bA743e925B53086",
            ETH_OPTION_ADDRESS="0x4BB4C3CDc7562f08e9910A0C7D8bB7e108861eB4",
            BTC_OPTION_ADDRESS="0xd0711b9eBE84b778483709CDe62BacFDBAE13623",
            TRADE_MODULE_ADDRESS="0xB8D20c2B7a1Ad2EE33Bc50eF10876eD3035b5e7b",
            STANDARD_RISK_MANAGER_ADDRESS="0x28c9ddF9A3B29c2E6a561c1BC520954e5A33de5D",
            BTC_PORTFOLIO_RISK_MANAGER_ADDRESS="0x45DA02B9cCF384d7DbDD7b2b13e705BADB43Db0D",
            ETH_PORTFOLIO_RISK_MANAGER_ADDRESS="0xe7cD9370CdE6C9b5eAbCe8f86d01822d3de205A0",
            CASH_ASSET="0x57B03E14d409ADC7fAb6CFc44b5886CAD2D5f02b",
            USDC_ASSET="0x6879287835A86F50f784313dBEd5E5cCC5bb8481",
            DEPOSIT_MODULE_ADDRESS="0x9B3FE5E5a3bcEa5df4E08c41Ce89C4e3Ff01Ace3",
            WITHDRAWAL_MODULE_ADDRESS="0x9d0E8f5b25384C7310CB8C6aE32C8fbeb645d083",
            TRANSFER_MODULE_ADDRESS="0x01259207A40925b794C8ac320456F7F6c8FE2636",
        ),
    ),
}

DEFAULT_REFERER = "0x9135BA0f495244dc0A5F029b25CDE95157Db89AD"

MSG_GAS_LIMIT = 100_000
DEPOSIT_GAS_LIMIT = 420_000
PAYLOAD_SIZE = 161
TARGET_SPEED = "FAST"


TOKEN_DECIMALS = {
    UnderlyingCurrency.ETH: 18,
    UnderlyingCurrency.BTC: 8,
    UnderlyingCurrency.USDC: 6,
    UnderlyingCurrency.LBTC: 8,
    UnderlyingCurrency.WEETH: 18,
    UnderlyingCurrency.OP: 18,
    UnderlyingCurrency.DRV: 18,
    UnderlyingCurrency.rswETH: 18,
    UnderlyingCurrency.rsETH: 18,
    UnderlyingCurrency.DAI: 18,
    UnderlyingCurrency.USDT: 6,
}
