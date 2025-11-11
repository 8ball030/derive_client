"""
Reads in the channels from the spec and generates websocket subscription methods.
"""

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

PACKAGE_DIR = Path(__file__).parent.parent / "derive_client"
JSON_SCHEMA_DIR = Path("specs") / "channels"
TEMPLATES_DIR = PACKAGE_DIR / "data" / "templates"
OUTPUT_DIR = PACKAGE_DIR / "_clients" / "websockets"


def collect_channel_schemas(schema_dir: Path):
    """Collect channel schemas from JSON files."""
    channel_schemas = []

    for schema_file in schema_dir.glob("*.json"):
        data = json.loads(schema_file.read_text())
        channel_schemas.append(data)

    return channel_schemas

def collect_enum_imports(schema_dir: Path):
    """Collect enum imports from JSON files."""
    enum_imports = set()

    for schema_file in schema_dir.glob("*.json"):
        data = json.loads(schema_file.read_text())
        for field in data.get("fields", []):
            if field.get("type") == "enum":
                enum_imports.add(field["enum_name"])

    return sorted(enum_imports)

def collect_schema_imports(schema_dir: Path):
    """Collect schema imports from JSON files."""
    schema_imports = set()

    for schema_file in schema_dir.glob("*.json"):
        data = json.loads(schema_file.read_text())
        breakpoint()
        schema_imports.add(data["name"])

    return sorted(schema_imports)


def main():
    print("Generating Websocket client...")
    template = Environment(loader=FileSystemLoader(TEMPLATES_DIR)).get_template("subscriptions.py.jinja")

    channel_schemas = collect_channel_schemas(JSON_SCHEMA_DIR)
    enum_imports = collect_enum_imports(JSON_SCHEMA_DIR)
    schema_imports = collect_schema_imports(JSON_SCHEMA_DIR)


    output = template.render(
        channel_schemas=channel_schemas,
        enum_imports=enum_imports,
        schema_imports=schema_imports
    )

    output_path = OUTPUT_DIR / "subscriptions.py"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output)
    print(f"  → {output_path}")


if __name__ == "__main__":
    main()
