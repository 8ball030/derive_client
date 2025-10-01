import ast
import json
import re
from pathlib import Path

import requests
from datamodel_code_generator import DataModelType, InputFileType, PythonVersion, generate
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TIMEOUT = 10
CUSTOM_HEADER = "# ruff: noqa: E741"


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
        use_subclass_enum=True,
        strict_nullable=True,
        use_double_quotes=True,
        field_constraints=True,
        disable_timestamp=True,
        custom_file_header=CUSTOM_HEADER,
        aliases=aliases,
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


class OptionalRewriter(ast.NodeTransformer):
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        self.generic_visit(node)
        if not is_struct_class(node):
            return node
        node.body = reorder_fields(node.body)
        return node


def patch_code(src: str) -> str:
    tree = ast.parse(src)
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


if __name__ == "__main__":
    base_url = "https://docs.derive.xyz"
    repo_root = Path(__file__).parent.parent
    input_path = Path("openapi-spec.json")
    output_path = repo_root / "derive_client" / "data" / "generated" / "models.py"
    generate_models(input_path=input_path, output_path=output_path)
    patch_pagination_to_optional(output_path)
    patch_file(output_path)
    print("Done.")
