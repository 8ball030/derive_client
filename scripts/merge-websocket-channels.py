import json
from pathlib import Path
from typing import Any


def merge_channel_schemas(channel_dir: Path, output_path: Path, exclude_files: set[str] | None = None) -> None:
    """
    Merge all JSON Schema files from channel_dir into a single schema file.

    Args:
        channel_dir: Directory containing individual channel JSON schema files
        output_path: Path where merged schema will be written
        exclude_files: Optional set of filenames to exclude (e.g., subscribe.json)
    """
    if exclude_files is None:
        exclude_files = {"subscribe.json", "unsubscribe.json"}  # These are likely request/response

    merged_definitions: dict[str, Any] = {}
    conflicts: dict[str, list[str]] = {}

    # Collect all schemas
    schema_files = sorted(channel_dir.glob("*.json"))

    print(f"Found {len(schema_files)} schema files")

    for schema_file in schema_files:
        if schema_file.name in exclude_files:
            print(f"Skipping {schema_file.name} (excluded)")
            continue

        print(f"Processing {schema_file.name}")

        with open(schema_file) as f:
            schema = json.load(f)

        # Extract definitions
        definitions = schema.get("definitions", {})

        for def_name, def_schema in definitions.items():
            if def_name in merged_definitions:
                # Check if it's actually the same definition
                if merged_definitions[def_name] == def_schema:
                    print(f"  ✓ {def_name} - duplicate but identical, skipping")
                    continue
                else:
                    # Conflict - different definitions with same name
                    if def_name not in conflicts:
                        conflicts[def_name] = [schema_file.name]
                    else:
                        conflicts[def_name].append(schema_file.name)
                    print(f"  ⚠ {def_name} - conflict detected!")
            else:
                merged_definitions[def_name] = def_schema
                print(f"  + {def_name}")

    # Report conflicts
    if conflicts:
        print("\n⚠️  CONFLICTS DETECTED:")
        for def_name, files in conflicts.items():
            print(f"  '{def_name}' defined differently in: {', '.join(files)}")
        print("\nConsider prefixing conflicting definitions with channel name.")
        print("Proceeding with first definition found for each conflict...")

    # Create merged schema
    merged_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Derive WebSocket Channel Schemas",
        "description": "Merged schemas for all WebSocket channels",
        "definitions": merged_definitions,
    }

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(merged_schema, f, indent=2)

    print(f"\n✓ Merged schema written to {output_path}")
    print(f"  Total definitions: {len(merged_definitions)}")
    print(f"  Conflicts: {len(conflicts)}")


if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent
    channel_dir = repo_root / "specs" / "channels"
    output_path = repo_root / "specs" / "websocket-channels.json"

    merge_channel_schemas(channel_dir, output_path)
