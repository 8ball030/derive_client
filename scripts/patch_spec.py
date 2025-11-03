#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Tuple

TARGET_TITLE = "erc20_details"
ANYOF_PAYLOAD = [{"type": "string"}, {"type": "integer"}]


def patch_node(node: Any) -> Tuple[Any, int]:
    """
    Recursively patch:
      additionalProperties: { title: "erc20_details", type: "string", ... }
    -> additionalProperties: { title: "erc20_details", anyOf: [...], ... }
    Returns (possibly-modified node, patches_applied)
    """
    changed = 0

    if isinstance(node, dict):
        # Patch additionalProperties blocks with the target title
        ap = node.get("additionalProperties")
        if (
            isinstance(ap, dict)
            and ap.get("title") == TARGET_TITLE
            and (ap.get("type") == "string" or "anyOf" not in ap)
        ):
            ap.pop("type", None)
            ap["anyOf"] = ANYOF_PAYLOAD
            node["additionalProperties"] = ap
            changed += 1

        # Recurse into dict values
        for k, v in list(node.items()):
            new_v, c = patch_node(v)
            if c:
                node[k] = new_v
            changed += c

    elif isinstance(node, list):
        for i, item in enumerate(list(node)):
            new_item, c = patch_node(item)
            if c:
                node[i] = new_item
            changed += c

    return node, changed


def main():
    p = argparse.ArgumentParser(description="Patch erc20_details additionalProperties to anyOf[string|integer].")
    p.add_argument("json_path", type=Path, help="Path to openapi-spec.json")
    p.add_argument("-o", "--out", type=Path, help="Output path (default: overwrite input)")
    args = p.parse_args()

    src = args.json_path
    out = args.out or src

    if not src.exists():
        print(f"Error: {src} not found", file=sys.stderr)
        sys.exit(1)

    with src.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data, count = patch_node(data)

    with out.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Patched occurrences: {count}")
    print(f"Written to: {out}")


if __name__ == "__main__":
    main()
