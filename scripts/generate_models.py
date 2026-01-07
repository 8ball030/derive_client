import ast
import re
from dataclasses import dataclass
from pathlib import Path

import libcst as cst
from datamodel_code_generator import DataModelType, InputFileType, PythonVersion, generate
from libcst import matchers as m

TIMEOUT = 10
CUSTOM_HEADER = "# ruff: noqa: E741,E501"


@dataclass
class ModelDefinition:
    """Represents a model or enum definition."""

    name: str
    type: str  # 'enum', 'struct', 'class'
    content_hash: str  # Normalized content for comparison
    original_code: str


@dataclass
class DeduplicationStrategy:
    """Strategy for handling a duplicate model."""

    target_name: str
    source_name: str
    action: str  # 'remove', 'inherit', 'keep'
    model_type: str  # 'enum', 'struct'


def generate_models(
    input_path: Path,
    output_path: Path,
    input_file_type: InputFileType,
):
    print(f"Generating models from {input_path.name} -> {output_path}")
    generate(
        input_=input_path,
        input_file_type=input_file_type,
        output=output_path,
        output_model_type=DataModelType.MsgspecStruct,
        target_python_version=PythonVersion.PY_311,
        reuse_model=True,
        use_subclass_enum=False,
        strict_nullable=True,
        use_double_quotes=True,
        field_constraints=True,
        disable_timestamp=True,
        custom_file_header=CUSTOM_HEADER,
    )
    print(f"Models generated at: {output_path}")


def patch_pagination_to_optional(path: Path) -> None:
    print("Patching models.py to make pagination optional")
    code = path.read_text()
    # Pydantic v2 and dataclasses
    code = re.sub(
        r"(\s)pagination:\s*PaginationInfoSchema(\s*(#.*)?$)",
        r"\1pagination: PaginationInfoSchema | None = None\2",
        code,
        flags=re.MULTILINE,
    )
    path.write_text(code)


def is_annassign(stmt: ast.stmt) -> bool:
    return isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)


def field_name(stmt: ast.AnnAssign) -> str | None:
    return stmt.target.id if isinstance(stmt.target, ast.Name) else None


def is_defaulted(stmt: ast.AnnAssign) -> bool:
    # x: T = ...
    return stmt.value is None


def reorder_fields(body: list[ast.stmt]) -> list[ast.stmt]:
    fields: list[ast.AnnAssign] = []
    others: list[ast.stmt] = []

    for s in body:
        if is_annassign(s):
            fields.append(s)  # type: ignore[arg-type]
        else:
            others.append(s)

    if not fields:
        return body

    non_defaults = [f for f in fields if not is_defaulted(f)]
    defaults = [f for f in fields if is_defaulted(f)]

    reordered_fields = defaults + non_defaults
    return reordered_fields + others


def _ensure_referral_default(node: ast.ClassDef) -> bool:
    referral_code = "'0x9135BA0f495244dc0A5F029b25CDE95157Db89AD'"
    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.target.id == "referral_code":
            stmt.value = ast.parse(referral_code).body[0].value
            ast.fix_missing_locations(node)
            return
    ann_node = ast.parse(f"referral_code: str = {referral_code}").body[0]
    node.body.insert(0, ann_node)
    ast.fix_missing_locations(node)


def update_get_tx_result_schema(node: ast.ClassDef) -> None:
    """Update fields annotated in OpenAPI spec as "str", but are deserialized into dict."""

    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            field_name = stmt.target.id
            if field_name == "data":
                stmt.annotation = ast.Name(id="dict", ctx=ast.Load())
            elif field_name == "error_log" and isinstance(stmt.annotation, ast.Subscript):
                stmt.annotation.slice = ast.Name(id="dict", ctx=ast.Load())


class OptionalRewriter(ast.NodeTransformer):
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        self.generic_visit(node)

        if node.name in {"PrivateOrderParamsSchema", "PrivateReplaceParamsSchema"}:
            _ensure_referral_default(node)

        if node.name == "PublicGetTransactionResultSchema":
            update_get_tx_result_schema(node)

        if node.name == "TriggerPriceType" and self._is_str_enum(node):
            self._add_type_ignore_to_index(node)

        if not is_struct_class(node):
            return node
        node.body = reorder_fields(node.body)
        return node

    def _is_str_enum(self, node: ast.ClassDef) -> bool:
        """Check if class inherits from both str and Enum."""
        base_names = {base.id for base in node.bases if isinstance(base, ast.Name)}
        return 'str' in base_names and 'Enum' in base_names

    def _add_type_ignore_to_index(self, node: ast.ClassDef) -> None:
        """Add type_comment to index assignment to suppress mypy error."""
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == 'index':
                        # Add type_comment which ast.unparse will render as # type: ignore
                        stmt.type_comment = 'ignore[assignment]'
                        return


def patch_code(src: str) -> str:
    tree = ast.parse(src)
    tracker = EnumTracker()
    tracker.visit(tree)

    fixer = DefaultValueFixer(tracker.enum_types, tracker.custom_types)
    tree = fixer.visit(tree)
    tree = OptionalRewriter().visit(tree)

    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def patch_file(path: Path) -> None:
    code = path.read_text()
    new_code = CUSTOM_HEADER + "\n" + patch_code(code)
    if new_code != code:
        path.write_text(new_code)


def is_struct_class(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if (
            isinstance(base, ast.Name)
            and base.id == "Struct"
            or isinstance(base, ast.Attribute)
            and base.attr == "Struct"
        ):
            return True
    return False


class EnumTracker(ast.NodeVisitor):
    """Track which imported names are Enums."""

    def __init__(self):
        self.enum_types: set[str] = set()
        self.custom_types: set[str] = {'Decimal'}  # Known custom types

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Check if class inherits from Enum or StrEnum
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in {'Enum', 'StrEnum', 'IntEnum'}:
                self.enum_types.add(node.name)
                break
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        # Track Decimal imports
        if node.module == 'decimal':
            for alias in node.names:
                if alias.name == 'Decimal':
                    self.custom_types.add('Decimal')


class DefaultValueFixer(ast.NodeTransformer):
    """Fix default values that need type coercion."""

    def __init__(self, enum_types: set[str], custom_types: set[str]):
        self.enum_types = enum_types
        self.custom_types = custom_types

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:
        if not isinstance(node.target, ast.Name) or node.value is None:
            return node

        type_name = self._get_type_name(node.annotation)
        if not type_name or not isinstance(node.value, ast.Constant):
            return node

        if node.value.value is None:
            return node

        # Fix known custom types that need constructor calls
        if type_name in self.custom_types or type_name in self.enum_types:
            node.value = ast.Call(func=ast.Name(id=type_name, ctx=ast.Load()), args=[node.value], keywords=[])

        return node

    def _get_type_name(self, annotation: ast.expr) -> str | None:
        """Extract the main type name from an annotation."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            # Handle Optional[X] -> X
            return self._get_type_name(annotation.slice)
        return None


def normalize_class_def(node: ast.ClassDef) -> str:
    """
    Create a normalized representation of a class for content comparison.
    Ignores the class name itself, focuses on structure and values.
    """

    parts = []

    # Get base classes
    bases = [ast.unparse(base) for base in node.bases]
    parts.append(f"bases:{','.join(sorted(bases))}")

    # Get all attributes/fields
    for item in node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            # Struct field: name: type = default
            field_name = item.target.id
            field_type = ast.unparse(item.annotation)
            field_default = ast.unparse(item.value) if item.value else "NODEFAULT"
            parts.append(f"field:{field_name}:{field_type}:{field_default}")

        elif isinstance(item, ast.Assign):
            # Enum member: name = value
            for target in item.targets:
                if isinstance(target, ast.Name):
                    member_name = target.id
                    member_value = ast.unparse(item.value)
                    parts.append(f"member:{member_name}:{member_value}")

    return "|".join(sorted(parts))


def extract_models_from_file(file_path: Path) -> dict[str, ModelDefinition]:
    """Extract all model definitions from a Python file."""

    code = file_path.read_text()
    tree = ast.parse(code)

    models = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        # Determine type
        base_names = {base.id for base in node.bases if isinstance(base, ast.Name)}
        base_attrs = {base.attr for base in node.bases if isinstance(base, ast.Attribute)}

        if 'Enum' in base_names or 'StrEnum' in base_names or 'IntEnum' in base_names:
            model_type = 'enum'
        elif 'Struct' in base_names or 'Struct' in base_attrs:
            model_type = 'struct'
        else:
            model_type = 'class'

        # Create normalized hash
        content_hash = normalize_class_def(node)

        # Store definition
        models[node.name] = ModelDefinition(
            name=node.name, type=model_type, content_hash=content_hash, original_code=ast.unparse(node)
        )

    return models


def find_duplicates(
    source_models: dict[str, ModelDefinition],
    target_models: dict[str, ModelDefinition],
) -> list[DeduplicationStrategy]:
    """
    Find models in target that are identical to models in source.
    Returns list of deduplication strategies.
    """

    # Build reverse index: content_hash -> source_name
    source_by_hash: dict[str, tuple[str, str]] = {}
    for name, model in source_models.items():
        if model.content_hash in source_by_hash:
            # Multiple source models with same content - use first one
            continue
        source_by_hash[model.content_hash] = (name, model.type)

    # Find matches and determine strategy
    strategies = []
    for target_name, target_model in target_models.items():
        if target_model.content_hash in source_by_hash:
            source_name, source_type = source_by_hash[target_model.content_hash]

            # Determine action based on model type and name
            if target_model.type == 'enum':
                action = 'remove'
                print(f"  ✓ {target_name} → {source_name} (enum, remove)")
            elif target_name == source_name:
                action = 'remove'
                print(f"  ✓ {target_name} → {source_name} (same name, remove)")
            else:
                action = 'inherit'
                print(f"  ✓ {target_name} → {source_name} (inherit)")

            strategies.append(
                DeduplicationStrategy(
                    target_name=target_name, source_name=source_name, action=action, model_type=target_model.type
                )
            )

    return strategies


class ModelDeduplicator(cst.CSTTransformer):
    """
    Deduplicate class definitions based on strategies.
    """

    def __init__(self, strategies: list[DeduplicationStrategy]):
        """
        Args:
            strategies: List of deduplication strategies
        """
        self.strategies_by_name = {s.target_name: s for s in strategies}
        self.removed_classes: set[str] = set()
        self.inherited_classes: set[str] = set()

    def leave_ClassDef(
        self,
        original_node: cst.ClassDef,
        updated_node: cst.ClassDef,
    ) -> cst.ClassDef | cst.RemovalSentinel:
        """Handle duplicate class definitions based on strategy."""
        class_name = updated_node.name.value

        if class_name not in self.strategies_by_name:
            return updated_node

        strategy = self.strategies_by_name[class_name]

        if strategy.action == 'remove':
            self.removed_classes.add(class_name)
            return cst.RemovalSentinel.REMOVE

        elif strategy.action == 'inherit':
            self.inherited_classes.add(class_name)

            new_class = updated_node.with_changes(
                bases=[cst.Arg(value=cst.Name(strategy.source_name))],
                body=cst.IndentedBlock(body=[cst.SimpleStatementLine(body=[cst.Pass()])]),
            )
            return new_class

        return updated_node

    def leave_Name(self, original_node: cst.Name, updated_node: cst.Name) -> cst.Name:
        """Rewrite references to removed duplicates."""

        name = updated_node.value

        if name in self.strategies_by_name:
            strategy = self.strategies_by_name[name]

            # Only rewrite if we removed the class entirely
            if strategy.action == 'remove':
                return updated_node.with_changes(value=strategy.source_name)

        return updated_node


def add_imports(module: cst.Module, imports_to_add: set[str]) -> cst.Module:
    """
    Add imports at the top of the file.

    Args:
        module: The CST module
        imports_to_add: Set of names to import
    """
    if not imports_to_add:
        return module

    import_names = [cst.ImportAlias(name=cst.Name(name)) for name in sorted(imports_to_add)]

    new_import = cst.SimpleStatementLine(
        body=[
            cst.ImportFrom(
                module=cst.Attribute(
                    value=cst.Attribute(value=cst.Name("derive_client"), attr=cst.Name("data_types")),
                    attr=cst.Name("generated_models"),
                ),
                names=import_names,
            )
        ]
    )

    body = list(module.body)
    insert_pos = 0

    for i, stmt in enumerate(body):
        if m.matches(stmt, m.SimpleStatementLine(body=[m.Import() | m.ImportFrom()])):
            insert_pos = i + 1
        elif not m.matches(stmt, m.EmptyLine() | m.SimpleStatementLine(body=[m.Expr(value=m.SimpleString())])):
            break

    body.insert(insert_pos, new_import)

    return module.with_changes(body=body)


def remove_redefined_classes(module: cst.Module, imported_names: set[str]) -> cst.Module:
    """
    Remove any class definitions that are already imported.
    This handles cases where classes weren't caught in the first deduplication pass.
    """

    class RedefinitionRemover(cst.CSTTransformer):
        def __init__(self, imported: set[str]):
            self.imported = imported
            self.removed = []

        def leave_ClassDef(
            self, original_node: cst.ClassDef, updated_node: cst.ClassDef
        ) -> cst.ClassDef | cst.RemovalSentinel:
            class_name = updated_node.name.value
            if class_name in self.imported:
                self.removed.append(class_name)
                return cst.RemovalSentinel.REMOVE
            return updated_node

    remover = RedefinitionRemover(imported_names)
    updated = module.visit(remover)

    if remover.removed:
        print(f"  Removed {len(remover.removed)} redefined classes: {', '.join(remover.removed)}")

    return updated


def deduplicate_channel_models(
    generated_models_path: Path,
    channel_models_path: Path,
    output_path: Path | None = None,
) -> None:
    """
    Main deduplication function.

    Args:
        generated_models_path: Path to generated_models.py (OpenAPI)
        channel_models_path: Path to channel_models.py
        output_path: Optional output path (defaults to overwriting channel_models_path)
    """
    if output_path is None:
        output_path = channel_models_path

    print("Extracting models from generated_models.py...")
    source_models = extract_models_from_file(generated_models_path)
    print(f"  Found {len(source_models)} models")

    print("\nExtracting models from channel_models.py...")
    target_models = extract_models_from_file(channel_models_path)
    print(f"  Found {len(target_models)} models")

    print("\nFinding duplicates...")
    strategies = find_duplicates(source_models, target_models)
    print(f"  Found {len(strategies)} duplicates to deduplicate")

    if not strategies:
        print("\n✓ No duplicates found, nothing to do!")
        return

    print("\nRewriting channel_models.py...")
    code = channel_models_path.read_text()
    module = cst.parse_module(code)

    deduplicator = ModelDeduplicator(strategies)
    updated_module = module.visit(deduplicator)

    imports_to_add = set()
    for strategy in strategies:
        imports_to_add.add(strategy.source_name)

    updated_module = add_imports(updated_module, imports_to_add)
    updated_module = remove_redefined_classes(updated_module, imports_to_add)
    output_path.write_text(updated_module.code)

    print("\n✓ Deduplicated channel_models.py")
    print(f"  Removed {len(deduplicator.removed_classes)} duplicate classes")
    print(f"  Converted {len(deduplicator.inherited_classes)} classes to inheritance")
    print(f"  Added imports for {len(imports_to_add)} models from generated_models.py")
    print(f"  Output written to: {output_path}")

    # Summary
    print("\n" + "=" * 60)
    print("Deduplication Summary:")
    print("=" * 60)

    removed = [s for s in strategies if s.action == 'remove']
    inherited = [s for s in strategies if s.action == 'inherit']

    if removed:
        print("\nRemoved (imported from generated_models):")
        for strategy in sorted(removed, key=lambda s: s.target_name):
            print(f"  {strategy.target_name:40s} → {strategy.source_name}")

    if inherited:
        print("\nConverted to inheritance:")
        for strategy in sorted(inherited, key=lambda s: s.target_name):
            print(f"  class {strategy.target_name}({strategy.source_name}): pass")


if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent
    input_path = repo_root / "specs" / "openapi-spec.json"
    output_path = repo_root / "derive_client" / "data_types" / "generated_models.py"

    generate_models(
        input_path=input_path,
        output_path=output_path,
        input_file_type=InputFileType.OpenAPI,
    )
    patch_pagination_to_optional(output_path)
    patch_file(output_path)

    ws_input = repo_root / "specs" / "websocket-channels.json"
    ws_output = repo_root / "derive_client" / "data_types" / "channel_models.py"
    generate_models(input_path=ws_input, output_path=ws_output, input_file_type=InputFileType.JsonSchema)
    patch_file(ws_output)
    deduplicate_channel_models(generated_models_path=output_path, channel_models_path=ws_output)

    print("Done.")
