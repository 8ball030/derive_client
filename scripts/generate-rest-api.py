import json
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import libcst as cst
from jinja2 import Environment, FileSystemLoader

PACKAGE_DIR = Path(__file__).parent.parent / "derive_client"
OPENAPI_SPEC = Path("specs") / "openapi-spec.json"
TEMPLATES_DIR = PACKAGE_DIR / "data" / "templates"
OUTPUT_DIR = PACKAGE_DIR / "_clients"
GENERATED_MODELS_PATH = PACKAGE_DIR / "data_types" / "generated_models.py"


@dataclass
class MethodInfo:
    name: str
    path: str
    request_type: str
    response_type: str
    result_type: str
    description: str


class ResponseSchemaParser(cst.CSTVisitor):
    """
    Parse generated_models.py to extract actual result field types
    from ResponseSchema classes, handling inheritance chains.
    """

    def __init__(self):
        self.result_types: dict[str, str] = {}
        self.class_bases: dict[str, list[str]] = {}
        self.class_fields: dict[str, dict[str, str]] = {}
        self.current_class: Optional[str] = None

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        # set current class so visit_AnnAssign knows where to store fields
        class_name = node.name.value
        self.current_class = class_name
        self.class_fields.setdefault(class_name, {})

        bases = []
        for base in node.bases:
            try:
                base_name = self._annotation_to_string(base.value)
            except Exception:
                base_name = ""
            base_name = base_name.split("[", 1)[0].strip()  # drop generics like ResponseSchema[Foo]
            if base_name:
                # If it's a dotted attribute like module.ResponseSchema, take the last part
                if "." in base_name:
                    base_name = base_name.rsplit(".", 1)[-1]
                bases.append(base_name)
        self.class_bases[class_name] = bases

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        # clear current class when leaving the class scope
        self.current_class = None

    def visit_AnnAssign(self, node: cst.AnnAssign) -> None:
        # Only capture annotated assignments that belong to a class we're inside
        if not self.current_class:
            return

        # target can be a Name, Attribute, Subscript, etc.
        target = node.target
        if isinstance(target, cst.Name):
            field_name = target.value
        else:
            # fallback to code for node (e.g., self.x)
            field_name = self._annotation_to_string(target)

        # annotation might be missing (rare), guard accordingly
        annotation_node = getattr(node, "annotation", None)
        if not annotation_node:
            return

        # extract annotation expression (annotation_node.annotation is the expression)
        annot_expr = annotation_node.annotation
        field_type = self._annotation_to_string(annot_expr).strip()

        # strip optional quotes for forward refs e.g. "'FooSchema'"
        if (field_type.startswith("'") and field_type.endswith("'")) or (
            field_type.startswith('"') and field_type.endswith('"')
        ):
            field_type = field_type[1:-1]

        self.class_fields.setdefault(self.current_class, {})[field_name] = field_type

    def _annotation_to_string(self, node: cst.BaseExpression) -> str:
        """Convert CST annotation node to a clean string representation"""
        try:
            text = cst.Module([]).code_for_node(node)
            return text.strip()
        except Exception:
            # fallback
            return repr(node)

    def get_result_type(self, response_schema_name: str) -> str:
        """
        Get the result field type for a given ResponseSchema class.
        Caches results to avoid repeated traversal.
        """
        if response_schema_name in self.result_types:
            return self.result_types[response_schema_name]

        result_type = self._find_result_field(response_schema_name)
        if not result_type:
            raise ValueError(f"Could not find result field for {response_schema_name}")

        self.result_types[response_schema_name] = result_type
        return result_type

    def _find_result_field(self, class_name: str, visited: Optional[set] = None) -> Optional[str]:
        """
        Find the 'result' field type by traversing the class hierarchy.
        Handles inheritance from base classes.
        """
        if visited is None:
            visited = set()
        if class_name in visited:
            return None
        visited.add(class_name)

        # Check if this class has a 'result' field
        fields = self.class_fields.get(class_name, {})
        if "result" in fields:
            return fields["result"]

        # If not found, check base classes
        for base in self.class_bases.get(class_name, []):
            if base in {"Struct", "object"}:
                continue
            result_type = self._find_result_field(base, visited)
            if result_type:
                return result_type
        return None


def extract_schema_names_from_type(type_annotation: str) -> set[str]:
    """
    Extract actual schema class names from a type annotation string.

    Filters out:
    - Generic types (List, Dict, Union, Optional, etc.)
    - Built-in types (str, int, float, bool, etc.)
    - Special types (Any, None, etc.)

    Examples:
        "List[AuctionResultSchema]" -> {"AuctionResultSchema"}
        "Union[str, int]" -> set()
        "Dict[str, InstrumentSchema]" -> {"InstrumentSchema"}
        "List[int]" -> set()
        "InstrumentPublicResponseSchema" -> {"InstrumentPublicResponseSchema"}
    """
    # Built-in types to skip
    BUILTINS = {
        "str",
        "int",
        "float",
        "bool",
        "bytes",
        "None",
        "Any",
        "dict",
        "list",
        "set",
        "tuple",
        "frozenset",
    }

    # Generic types to skip
    GENERICS = {
        "List",
        "Dict",
        "Set",
        "Tuple",
        "FrozenSet",
        "Union",
        "Optional",
        "Literal",
        "Annotated",
        "Sequence",
        "Mapping",
        "Iterable",
    }

    # Find all potential class names (words that start with uppercase or contain Schema)
    # This regex finds capitalized identifiers
    pattern = r'\b([A-Z][a-zA-Z0-9_]*)\b'
    matches = re.findall(pattern, type_annotation)

    schema_names = set()
    for match in matches:
        if match in GENERICS or match in BUILTINS:
            continue
        schema_names.add(match)

    return schema_names


def parse_generated_models() -> ResponseSchemaParser:
    """
    Parse the generated_models.py file to extract result field types
    from ResponseSchema classes.
    """
    if not GENERATED_MODELS_PATH.exists():
        raise FileNotFoundError(f"Generated models not found at {GENERATED_MODELS_PATH}. Run model generation first.")

    source_code = GENERATED_MODELS_PATH.read_text()
    tree = cst.parse_module(source_code)

    parser = ResponseSchemaParser()
    tree.visit(parser)

    return parser


def parse_openapi_for_rpc(spec_path: Path, parser: ResponseSchemaParser):
    """
    Parse OpenAPI spec for RPC methods, using ResponseSchemaParser
    to get actual result field types.
    """

    data = json.loads(spec_path.read_text())

    public_methods = []
    private_methods = []
    schema_imports = set()

    for path, spec in data["paths"].items():
        post_spec = spec["post"]
        request_ref = post_spec["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        response_ref = post_spec["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]

        name = path.split("/")[-1]
        request_type = request_ref.split("/")[-1]
        response_type = response_ref.split("/")[-1]

        # Get actual result type from generated models
        result_type = parser.get_result_type(response_type)

        description = post_spec["description"]

        # Extract schema names from types (filter out generics and builtins)
        schema_imports.add(request_type)
        schema_imports.update(extract_schema_names_from_type(result_type))

        method = MethodInfo(
            name=name,
            path=path,
            request_type=request_type,
            response_type=response_type,
            result_type=result_type,
            description=description,
        )

        if path.startswith("/public"):
            public_methods.append(method)
        else:
            private_methods.append(method)

    return public_methods, private_methods, schema_imports


def format_docstring(text: str, width: int = 88) -> str:
    """Format text as a proper Python docstring"""

    if not text:
        return ""

    text = text.replace("<br />", "\n").replace("<br/>", "\n")
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    wrapped = []
    for para in paragraphs:
        wrapped.extend(textwrap.wrap(para, width=width - 8))
        wrapped.append("")

    if wrapped and not wrapped[-1]:
        wrapped.pop()

    return "\n        ".join(wrapped)


def generate_files(spec: Path):
    """Generate all API files from templates."""

    # First, parse the generated models to extract result types
    print("Parsing generated_models.py for result types...")
    parser = parse_generated_models()
    print(f"  → Found {len(parser.class_fields)} classes")

    # Parse OpenAPI spec with the parser
    print("Parsing OpenAPI spec...")
    public_methods, private_methods, schema_imports = parse_openapi_for_rpc(spec, parser)
    print(f"  → {len(public_methods)} public methods")
    print(f"  → {len(private_methods)} private methods")
    print(f"  → {len(schema_imports)} schema imports")

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    env.filters['format_docstring'] = format_docstring

    print("\nGenerating endpoints.py...")
    template = env.get_template("endpoints.py.jinja")
    output = template.render(
        public_methods=public_methods,
        private_methods=private_methods,
    )
    output_path = OUTPUT_DIR / "rest" / "endpoints.py"
    output_path.write_text(output)
    print(f"  → {output_path}")

    print("Generating rest/http/api.py...")
    template = env.get_template("api.py.jinja")
    output = template.render(
        is_async=False,
        api_prefix="",
        public_methods=public_methods,
        private_methods=private_methods,
        schema_imports=sorted(schema_imports),
    )
    output_path = OUTPUT_DIR / "rest" / "http" / "api.py"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output)
    print(f"  → {output_path}")

    print("Generating rest/async_http/api.py...")
    output = template.render(
        is_async=True,
        api_prefix="Async",
        public_methods=public_methods,
        private_methods=private_methods,
        schema_imports=sorted(schema_imports),
    )
    output_path = OUTPUT_DIR / "rest" / "async_http" / "api.py"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output)
    print(f"  → {output_path}")

    print("\n✓ REST API generation complete!")


if __name__ == "__main__":
    if not OPENAPI_SPEC.exists():
        raise FileNotFoundError(f"OpenAPI spec not found at {OPENAPI_SPEC}")

    generate_files(OPENAPI_SPEC)
