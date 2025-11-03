import ast
import json
import re
from pathlib import Path

import requests
from datamodel_code_generator import DataModelType, InputFileType, PythonVersion, generate
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TIMEOUT = 10
CUSTOM_HEADER = "# ruff: noqa: E741,E501"


def make_session_with_retries(
    total: int = 3,
    backoff_factor: float = 0.3,
    status_forcelist: tuple = (500, 502, 504),
    allowed_methods: tuple = ("GET", "POST"),
) -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=total,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=allowed_methods,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def download_openapi_specs(openapi_specs_path: str, base_url: str, dest_dir: Path) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    index_url = f"{base_url}/openapi"

    with make_session_with_retries() as session:
        print(f"Fetching OpenAPI index: {index_url}")
        resp = session.get(index_url, timeout=TIMEOUT)
        resp.raise_for_status()
        html = resp.text

        text_pattern = r'<a[^>]*href="(/openapi/[^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(text_pattern, html)

        if not matches:
            raise RuntimeError(f"No openapi links found at {index_url}")

        saved_files = []
        for href, text in matches:
            spec_url = base_url + href
            print(f"Downloading: {spec_url}")
            resp = session.get(spec_url, timeout=TIMEOUT)
            resp.raise_for_status()
            file_name = text.replace(" ", "").replace(".", "_")
            file_path = (openapi_specs_path / file_name).with_suffix(".json")
            file_path.write_text(json.dumps(resp.json(), indent=2))
            saved_files.append(file_path)
            print(f"Saved OpenAPI spec at: {file_path}")
    return saved_files


def generate_models(input_path: Path, output_path: Path):
    print(f"Generating models from {input_path.name} -> {output_path}")
    generate(
        input_=input_path,
        input_file_type=InputFileType.OpenAPI,
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


if __name__ == "__main__":
    base_url = "https://docs.derive.xyz"
    repo_root = Path(__file__).parent.parent
    input_path = repo_root / "openapi-spec.json"
    output_path = repo_root / "derive_client" / "data_types" / "generated_models.py"

    generate_models(input_path=input_path, output_path=output_path)
    patch_pagination_to_optional(output_path)
    patch_file(output_path)
    print("Done.")
