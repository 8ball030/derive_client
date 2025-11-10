"""Generate the code reference pages and navigation."""

import inspect
import importlib
from pathlib import Path

import mkdocs_gen_files

REPO_ROOT = Path(__file__).parent.parent
PACKAGE_DIR = REPO_ROOT / "derive_client"


def get_public_members(module_path: str, class_name: str) -> list[str]:
    """Extract all public (non-private) members from a class.

    Args:
        module_path: Full module path, e.g., "derive_client._clients.rest.http.orders"
        class_name: Class name, e.g., "OrderOperations"

    Returns:
        List of public member names
    """

    # Import the module and get the class
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)

    # Get all members, filter out private ones
    public_members = [name for name, _ in inspect.getmembers(cls) if not name.startswith('_') or name in ('__init__',)]

    return public_members


def generate_client_docs(nav: mkdocs_gen_files.Nav):
    """Generate docs for HTTP/Async clients - show public interface only."""

    clients = {
        "HTTPClient": "derive_client._clients.rest.http.client",
        "AsyncHTTPClient": "derive_client._clients.rest.async_http.client",
    }

    # Public members we want to document
    public_members = [
        "__init__",
        "connect",
        "disconnect",
        "account",
        "active_subaccount",
        "bridge",
        "fetch_subaccount",
        "fetch_subaccounts",
        "cached_subaccounts",
        "markets",
        "transactions",
        "orders",
        "positions",
        "rfq",
        "mmp",
        "trades",
        "timeout",
        "__enter__",
        "__exit__",
    ]

    for display_name, module_path in clients.items():
        doc_path = Path("clients", f"{display_name.lower()}.md")
        full_doc_path = Path("reference", doc_path)

        nav[("Clients", display_name)] = doc_path.as_posix()

        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            fd.write(f"# {display_name}\n\n")
            fd.write(f"::: {module_path}.{display_name}\n")
            fd.write("    options:\n")
            fd.write("      show_root_heading: false\n")
            fd.write("      heading_level: 2\n")
            fd.write("      members_order: source\n")
            fd.write(f"      members: {public_members}\n")
            fd.write("      show_bases: false\n")
            fd.write("      show_source: false\n")
            fd.write("      inherited_members: false\n")
            fd.write("      show_signature_annotations: true\n")


def generate_account_docs(nav: mkdocs_gen_files.Nav):
    """Generate docs for account classes - show public methods only."""

    accounts = {
        "LightAccount": "derive_client._clients.rest.http.account",
        "Subaccount": "derive_client._clients.rest.http.subaccount",
    }

    lightaccount_public_members = [
        "__init__",
        "from_api",
        "state",
        "address",
        "refresh",
        "build_register_session_key_tx",
        "register_session_key",
        "deregister_session_key",
        "register_scoped_session_key",
        "session_keys",
        "edit_session_key",
        "get_all_portfolios",
        "create_subaccount",
        "get_subaccounts",
        "get",
        "__repr__",
    ]

    subaccount_public_members = [
        "__init__",
        "from_api",
        "refresh",
        "state",
        "margin_type",
        "currency",
        "id",
        "markets",
        "transactions",
        "orders",
        "positions",
        "rfq",
        "trades",
        "mmp",
        "sign_action",
        "__repr__",
        "__lt__",
    ]
    public = lightaccount_public_members, subaccount_public_members

    for public_members, (display_name, module_path) in zip(public, accounts.items()):
        doc_path = Path("accounts", f"{display_name.lower()}.md")
        full_doc_path = Path("reference", doc_path)

        nav[("Accounts", display_name)] = doc_path.as_posix()

        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            fd.write(f"# {display_name}\n\n")
            fd.write(f"::: {module_path}.{display_name}\n")
            fd.write("    options:\n")
            fd.write("      show_root_heading: false\n")
            fd.write("      heading_level: 2\n")
            fd.write("      members_order: source\n")
            fd.write(f"      members: {public_members}\n")
            fd.write("      show_bases: false\n")
            fd.write("      show_source: false\n")
            fd.write("      inherited_members: false\n")
            fd.write("      show_signature_annotations: true\n")


def generate_operation_docs(nav: mkdocs_gen_files.Nav):
    """Generate docs for operation classes - show all public methods."""

    operations = {
        "MarketOperations": "derive_client._clients.rest.http.markets",
        "OrderOperations": "derive_client._clients.rest.http.orders",
        "PositionOperations": "derive_client._clients.rest.http.positions",
        "RFQOperations": "derive_client._clients.rest.http.rfq",
        "MMPOperations": "derive_client._clients.rest.http.mmp",
        "TradeOperations": "derive_client._clients.rest.http.trades",
        "TransactionOperations": "derive_client._clients.rest.http.transactions",
    }

    for display_name, module_path in operations.items():
        doc_path = Path("operations", f"{display_name.lower()}.md")
        full_doc_path = Path("reference", doc_path)

        nav[("Operations", display_name)] = doc_path.as_posix()

        public_members = get_public_members(module_path, display_name)

        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            fd.write(f"# {display_name}\n\n")
            fd.write("!!! info\n")
            fd.write(f"    Access via `client.{display_name.lower().replace('operations', '')}` property.\n\n")
            fd.write(f"::: {module_path}.{display_name}\n")
            fd.write("    options:\n")
            fd.write("      show_root_heading: false\n")
            fd.write("      heading_level: 2\n")
            fd.write("      members_order: source\n")
            fd.write(f"      members: {public_members}\n")
            fd.write("      show_bases: false\n")
            fd.write("      show_source: false\n")
            fd.write("      inherited_members: false\n")


def generate_datatype_docs(nav: mkdocs_gen_files.Nav):
    """Generate docs for data types with specialized settings per type."""

    # Enums - show all members
    doc_path = Path("data_types", "enums.md")
    full_doc_path = Path("reference", doc_path)
    nav[("Data Types", "Enums")] = doc_path.as_posix()

    # Enums - document each enum class
    enums = [
        "ChainID",
        "TxStatus",
        "BridgeDirection",
        "BridgeType",
        "GasPriority",
        "UnderlyingCurrency",
        "Currency",
        "Environment",
        "EthereumJSONRPCErrorCode",
        "DeriveJSONRPCErrorCode",
    ]

    for enum_name in enums:
        doc_path = Path("data_types", "enums", f"{enum_name.lower()}.md")
        full_doc_path = Path("reference", doc_path)
        nav[("Data Types", "Enums", enum_name)] = doc_path.as_posix()

        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            fd.write(f"# {enum_name}\n\n")
            fd.write(f"::: derive_client.data_types.enums.{enum_name}\n")
            fd.write("    options:\n")
            fd.write("      show_root_heading: false\n")
            fd.write("      heading_level: 2\n")
            fd.write("      show_source: true\n")
            fd.write("      members: true\n")  # Show enum values

    # Models - show all fields and methods
    doc_path = Path("data_types", "models.md")
    full_doc_path = Path("reference", doc_path)
    nav[("Data Types", "Models")] = doc_path.as_posix()

    models = [
        # "DeriveContractAddresses",
        "EnvConfig",
        # "PHexBytes",
        "ChecksumAddress",
        # "TxHash",
        # "Wei",
        # "TypedFilterParams",
        # "TypedLogReceipt",
        # "TypedTxReceipt",
        # "TypedSignedTransaction",
        # "TypedTransaction",
        # "TokenData",
        # "MintableTokenData",
        # "NonMintableTokenData",
        # "DeriveAddresses",
        # "BridgeContext",
        "BridgeTxDetails",
        "PreparedBridgeTx",
        # "TxResult",
        "BridgeTxResult",
        # "RPCEndpoints",
        # "FeeHistory",
        # "FeeEstimate",
        # "FeeEstimates",
        "PositionTransfer",
    ]

    for model_name in models:
        doc_path = Path("data_types", "models", f"{model_name.lower()}.md")
        full_doc_path = Path("reference", doc_path)
        nav[("Data Types", "Models", model_name)] = doc_path.as_posix()

        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            fd.write(f"# {model_name}\n\n")
            fd.write(f"::: derive_client.data_types.models.{model_name}\n")
            fd.write("    options:\n")
            fd.write("      show_root_heading: false\n")
            fd.write("      heading_level: 2\n")
            fd.write("      show_source: true\n")
            fd.write("      members: true\n")

    doc_path = Path("data_types", "exceptions.md")
    full_doc_path = Path("reference", doc_path)
    nav[("Data Types", "Exceptions")] = doc_path.as_posix()

    exceptions = [
        "NotConnectedError",
        "ApiException",
        "EthereumJSONRPCException",
        "DeriveJSONRPCException",
        "BridgeEventParseError",
        "BridgeRouteError",
        "NoAvailableRPC",
        "InsufficientNativeBalance",
        "InsufficientTokenBalance",
        "BridgePrimarySignerRequiredError",
        "TxReceiptMissing",
        "FinalityTimeout",
        "TxPendingTimeout",
        "TransactionDropped",
        "BridgeEventTimeout",
        "PartialBridgeResult",
        "StandardBridgeRelayFailed",
    ]

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        fd.write("# Exceptions\n\n")

        for exc_name in exceptions:
            fd.write(f"## {exc_name}\n\n")
            fd.write(f"::: derive_client.exceptions.{exc_name}\n")
            fd.write("    options:\n")
            fd.write("      show_root_heading: false\n")
            fd.write("      heading_level: 3\n")
            fd.write("      show_bases: true\n")
            fd.write("      show_source: true\n")
            fd.write("      members: false\n\n")


def build_nav_and_files():
    """Build complete navigation and documentation files."""
    nav = mkdocs_gen_files.Nav()

    # Generate each section with appropriate settings
    generate_client_docs(nav)
    generate_account_docs(nav)
    generate_operation_docs(nav)
    generate_datatype_docs(nav)

    # Write navigation
    with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
        nav_file.writelines(nav.build_literate_nav())


if __name__ == "__main__":
    build_nav_and_files()
