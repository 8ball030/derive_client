import json
import textwrap
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

PACKAGE_DIR = Path(__file__).parent.parent / "derive_client"
OPENAPI_SPEC = Path("specs") / "openapi-spec.json"
TEMPLATES_DIR = PACKAGE_DIR / "data" / "templates"
OUTPUT_DIR = PACKAGE_DIR / "_clients"


@dataclass
class MethodInfo:
    name: str
    path: str
    request_type: str
    response_type: str
    result_type: str
    description: str


def parse_openapi_spec(spec_path: Path):
    """Parse OpenAPI spec and extract method info."""

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
        result_type = response_type.replace("Response", "Result")
        description = post_spec["description"]

        schema_imports.update([request_type, response_type])

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

    public_methods, private_methods, schema_imports = parse_openapi_spec(spec)

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    env.filters['format_docstring'] = format_docstring

    print("Generating endpoints.py...")
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


if __name__ == "__main__":
    if not OPENAPI_SPEC.exists():
        raise FileNotFoundError(OPENAPI_SPEC)

    generate_files(OPENAPI_SPEC)
