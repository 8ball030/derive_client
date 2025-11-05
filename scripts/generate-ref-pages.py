"""Generate the code reference pages and navigation."""

from pathlib import Path

import mkdocs_gen_files

REPO_ROOT = Path(__file__).parent.parent
PACKAGE_DIR = REPO_ROOT / "derive_client"


def build_nav_and_files():
    nav = mkdocs_gen_files.Nav()

    # Core client classes
    core_modules = {
        "HTTPClient": "derive_client._clients.rest.http.client",
        "AsyncHTTPClient": "derive_client._clients.rest.async_http.client",
    }

    # Account classes
    account_modules = {
        "LightAccount": "derive_client._clients.rest.http.account",
        "Subaccount": "derive_client._clients.rest.http.subaccount",
    }

    # Operation classes (sync)
    operation_modules = {
        "MarketOperations": "derive_client._clients.rest.http.markets",
        "OrderOperations": "derive_client._clients.rest.http.orders",
        "PositionOperations": "derive_client._clients.rest.http.positions",
        "RFQOperations": "derive_client._clients.rest.http.rfq",
        "MMPOperations": "derive_client._clients.rest.http.mmp",
        "TradeOperations": "derive_client._clients.rest.http.trades",
        "TransactionOperations": "derive_client._clients.rest.http.transactions",
    }

    # Data types and utilities
    other_modules = {
        "Exceptions": "derive_client.exceptions",
        "Enums": "derive_client.data_types.enums",
        "Models": "derive_client.data_types.models",
    }

    # Generate organized structure
    sections = [
        ("Clients", core_modules),
        ("Accounts", account_modules),
        ("Operations", operation_modules),
        ("Data Types", other_modules),
    ]

    for section_name, modules in sections:
        for display_name, module_path in modules.items():
            # Create a clean path: reference/clients/http_client.md
            section_slug = section_name.lower().replace(" ", "_")
            file_slug = display_name.lower().replace(" ", "_")
            doc_path = Path(section_slug, f"{file_slug}.md")
            full_doc_path = Path("reference", doc_path)

            # Navigation structure
            nav_parts = (section_name, display_name)
            nav[nav_parts] = doc_path.as_posix()

            with mkdocs_gen_files.open(full_doc_path, "w") as fd:
                fd.write(f"# {display_name}\n\n")
                fd.write(f"::: {module_path}\n")
                fd.write("    options:\n")
                fd.write("      show_root_heading: false\n")
                fd.write("      heading_level: 2\n")
                fd.write("      filters:\n")
                fd.write("        - '!^_'\n")
                fd.write("      members_order: source\n")

    with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
        nav_file.writelines(nav.build_literate_nav())


if __name__ == "__main__":
    build_nav_and_files()
