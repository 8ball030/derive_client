import ast
from copy import deepcopy
from pathlib import Path

from datamodel_code_generator import DataModelType, InputFileType, PythonVersion, generate

from scripts.generate_models import patch_file

TIMEOUT = 10
CUSTOM_HEADER = "# ruff: noqa: E741,E501"
CHANNEL_ENUM_TO_OPENAPI_ALIAS_OVERRIDE = {
    "TxStatus": ["TxStatus2", "TxStatus"],
    "TxStatus2": ["TxStatus2", "TxStatus"],
    "CancelReason": ["CancelReason1", "CancelReason"],
}


def generate_models(
    input_path: Path,
    output_path: Path,
):
    print(f"Generating models from {input_path.name} -> {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generate(
        input_=input_path,
        input_file_type=InputFileType.JsonSchema,
        output=output_path,
        output_model_type=DataModelType.MsgspecStruct,
        target_python_version=PythonVersion.PY_311,
        reuse_model=True,
        use_subclass_enum=False,
        strict_nullable=True,
        use_double_quotes=True,
        field_constraints=True,
        disable_timestamp=True,
    )
    print(f"Models generated at: {output_path}")


def extract_enums_from_generated_file(file_path: Path, remove=True) -> dict[str, ast.ClassDef]:
    """
    Extract enum class definitions from a generated Python file.
    Remove and return a dictionary mapping enum names to their AST nodes.
    """
    tree = ast.parse(file_path.read_text())
    enums = {}
    nodes_to_remove = []
    for node in tree.body:  # Iterate only top-level nodes
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "Enum":
                    enums[node.name] = deepcopy(node)  # Store a copy
                    nodes_to_remove.append(node)
                    break

    if remove:
        for node in nodes_to_remove:
            tree.body.remove(node)
        file_path.write_text(ast.unparse(tree))
    return enums


# Ast to ensure that all = None attributes are Optional types
def patch_defaults_to_optional(file_path: Path):
    tree = ast.parse(file_path.read_text())

    class OptionalPatcher(ast.NodeTransformer):
        def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AnnAssign:
            # Wrap the existing annotation in Optional[] if not already Optional
            if (
                isinstance(node.value, ast.Constant)
                and node.value.value is None
                and not (
                    isinstance(node.annotation, ast.Subscript)
                    and isinstance(node.annotation.value, ast.Name)
                    and node.annotation.value.id == "Optional"
                )
            ):
                node.annotation = ast.Subscript(
                    value=ast.Name(id="Optional", ctx=ast.Load()), slice=node.annotation, ctx=ast.Load()
                )
            return node

    patched_tree = OptionalPatcher().visit(tree)
    file_path.write_text(ast.unparse(patched_tree))


if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent
    input_directory = repo_root / "specs" / "channels"
    output_directory = repo_root / "derive_client" / "data_types" / "channels"

    open_api_models_file = repo_root / "derive_client" / "data_types" / "generated_models.py"
    open_api_enums = extract_enums_from_generated_file(open_api_models_file, remove=False)

    channel_enums = {}
    conflicting_enums = []
    conflicting_openapi_enums = []
    for input_path in input_directory.glob("*.json"):
        name = "_".join(input_path.name.split(".")[:-1]) + ".py"

        name = name.replace("channel_", "").replace("subaccount_id_", "")
        if "subaccount_id" in input_path.name:
            # Skip subaccount_id schemas for now
            output_path = output_directory / "private" / name
        else:
            output_path = output_directory / "public" / name
        print(f"Processing {input_path.name}...")
        generate_models(
            input_path=input_path,
            output_path=output_path,
        )
        patch_file(output_path)
        patch_defaults_to_optional(output_path)
        enums = extract_enums_from_generated_file(output_path)
        # we raise an error if there are duplicate enum names
        open_api_imports = []
        required_new_imports = []
        for enum_name in enums:
            # check existing openapi enums
            if aliases := CHANNEL_ENUM_TO_OPENAPI_ALIAS_OVERRIDE.get(enum_name):
                found = False
                for open_alias in aliases:
                    openapi_enum = open_api_enums[open_alias]
                    alias_enum = ast.unparse(openapi_enum).replace(open_alias, enum_name)
                    new_enum = ast.unparse(enums[enum_name])
                    if alias_enum == new_enum:
                        found = True
                        open_api_imports.append(
                            f"from derive_client.data_types.generated_models import {open_alias} as {enum_name}"
                        )
                        break
                if not found:
                    conflicting_openapi_enums.append({enum_name: (alias_enum, new_enum)})
                    raise ValueError(f"Conflicting enum {enum_name} found between channel models and openapi models.")
                else:
                    continue

            # simple direct matches
            if enum_name in channel_enums:
                current_enum = ast.unparse(channel_enums[enum_name])
                new_enum = ast.unparse(enums[enum_name])
                if current_enum != new_enum:
                    conflicting_enums.append({enum_name: (current_enum, new_enum)})
                    raise ValueError(f"Conflicting enum {enum_name} found across channel models.")
            else:
                channel_enums[enum_name] = enums[enum_name]

        # we add imports to the top of the file
        if open_api_imports:
            tree = ast.parse(output_path.read_text())
            import_nodes = [ast.parse(import_line).body[0] for import_line in open_api_imports]
            tree.body = import_nodes + tree.body
            output_path.write_text(ast.unparse(tree))
        # we add all channel enums used in this file as imports
        if channel_enums:
            tree = ast.parse(output_path.read_text())
            import_lines = [
                f"from derive_client.data_types.channels.enums import {enum_name}"
                for enum_name in channel_enums
                if enum_name in enums
            ]
            import_nodes = [ast.parse(import_line).body[0] for import_line in import_lines]
            tree.body = import_nodes + tree.body
            output_path.write_text(ast.unparse(tree))

    # at this point we have extracted all enums from all channel models,

    # we check if is already defined in openapi_spec generated models.
    # now we write the enums to a separate file
    enums_output_path = output_directory / "enums.py"
    print(f"Writing enums to {enums_output_path}...")
    enums_output_path.write_text(CUSTOM_HEADER + "\n\nfrom enum import Enum\n\n")
    for enum_name, enum_node in channel_enums.items():
        with enums_output_path.open("a") as f:
            f.write(ast.unparse(enum_node))
            f.write("\n\n")

    if conflicting_enums:
        print("Conflicting enums found across channel models:")
        for conflict in conflicting_enums:
            for enum_name, (original, new) in conflict.items():
                print(f"Conflict for enum {enum_name}:\nOriginal:\n{original}\nNew:\n{new}\n")
        raise ValueError("Conflicting enums found across channel models. See above for details.")
    if conflicting_openapi_enums:
        print("Conflicting enums found between channel models and openapi models:")
        for conflict in conflicting_openapi_enums:
            for enum_name, (original, new) in conflict.items():
                print(f"Conflict for enum {enum_name}:\nOpenAPI Model:\n{original}\nChannel Model:\n{new}\n")
        raise ValueError("Conflicting enums found between channel models and openapi models. See above for details.")

    # print("Patching pagination fields to be optional...")

    # patch_pagination_to_optional(output_path)
    # print("Done.")
