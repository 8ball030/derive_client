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
CHANNELS_DIR = Path("specs") / "channels"
TEMPLATES_DIR = PACKAGE_DIR / "data" / "templates"
OUTPUT_DIR = PACKAGE_DIR / "_clients"
GENERATED_MODELS = PACKAGE_DIR / "data_types" / "generated_models.py"

# Mapping from docs - which channels are public vs private
PUBLIC_CHANNELS = {
    "orderbook.instrument_name.group.depth",
    "ticker.instrument_name.interval",
    "spot_feed.currency",
    "trades.instrument_name",
    "trades.instrument_type.currency",
    "trades.instrument_type.currency.tx_status",
    "margin.watch",
    "auctions.watch",
}

PRIVATE_CHANNELS = {
    "subaccount_id.best.quotes",
    "subaccount_id.quotes",
    "subaccount_id.trades.tx_status",
    "wallet.rfqs",
    "subaccount_id.balances",
    "subaccount_id.orders",
    "subaccount_id.trades",
}


@dataclass
class MethodInfo:
    name: str
    path: str
    request_type: str
    response_type: str
    result_type: str
    description: str


@dataclass
class ChannelInfo:
    name: str  # Python method name
    channel_pattern: str  # e.g., "{subaccount_id}.best.quotes"
    params_type: str  # ChannelParamsSchema
    notification_type: str  # NotificationSchema
    description: str
    params: list[str]  # e.g., ["subaccount_id", "instrument_name"]


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
        if response_schema_name in self.result_types:
            return self.result_types[response_schema_name]

        result_type = self._find_result_field(response_schema_name)
        if not result_type:
            raise ValueError(f"Could not find result field for {response_schema_name}")

        self.result_types[response_schema_name] = result_type
        return result_type

    def _find_result_field(self, class_name: str, visited: Optional[set] = None) -> Optional[str]:
        if visited is None:
            visited = set()
        if class_name in visited:
            return None
        visited.add(class_name)

        fields = self.class_fields.get(class_name, {})
        if "result" in fields:
            return fields["result"]

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


def parse_channel_name(filename: str) -> tuple[str, list[str]]:
    """
    Parse channel filename to extract channel pattern and parameters.

    Example:
        "channel.subaccount_id.best.quotes.json"
        -> ("subaccount_id.best.quotes", ["subaccount_id"])
    """
    # Remove "channel." prefix and ".json" suffix
    name = filename.replace("channel.", "").replace(".json", "")

    # Extract parameters (lowercase words that appear to be placeholders)
    params = []
    parts = name.split(".")

    # Common parameter patterns
    param_patterns = {
        "subaccount_id",
        "instrument_name",
        "instrument_type",
        "currency",
        "group",
        "depth",
        "interval",
    }

    for part in parts:
        if part in param_patterns:
            params.append(part)

    return name, params


def to_python_method_name(channel_name: str) -> str:
    """
    Convert channel name to Python method name.

    To avoid conflicts, include parameter types in method name for disambiguation.

    Examples:
        "trades.instrument_name" -> "trades_by_instrument_name"
        "trades.instrument_type.currency" -> "trades_by_instrument_type"
        "subaccount_id.best.quotes" -> "best_quotes"
    """
    parts = channel_name.split(".")

    # Parameter names that indicate "by X"
    param_indicators = {"instrument_name", "instrument_type", "currency", "subaccount_id", "wallet"}

    # Build method name with "by_X" suffixes for clarity
    method_parts = []
    found_params = []

    for part in parts:
        if part in param_indicators:
            found_params.append(part)
        else:
            method_parts.append(part)

    # Base name
    base_name = "_".join(method_parts)

    # Add "by_X" suffixes if we found parameters
    if found_params:
        # Use first param as primary disambiguator
        suffix = f"by_{found_params[0]}"
        return f"{base_name}_{suffix}"

    return base_name


def extract_schema_types(schema_data: dict) -> tuple[str, str]:
    """
    Extract the channel params and notification schema types from JSON schema.

    Returns (params_type, notification_type)
    """
    definitions = schema_data.get("definitions", {})

    # Find the PubSubSchema (top-level schema)
    pubsub_schema = None
    for name, defn in definitions.items():
        if "PubSubSchema" in name:
            pubsub_schema = defn
            break

    if not pubsub_schema:
        return "dict", "dict"

    # Extract types from properties
    props = pubsub_schema.get("properties", {})

    params_ref = props.get("channel_params", {}).get("$ref", "")
    params_type = params_ref.split("/")[-1] if params_ref else "dict"

    notification_ref = props.get("notification", {}).get("$ref", "")
    notification_type = notification_ref.split("/")[-1] if notification_ref else "dict"

    return params_type, notification_type


def parse_channel_schemas(channels_dir: Path):
    """Parse all channel JSON schemas."""

    public_channels = []
    private_channels = []
    schema_imports = set()

    for schema_file in sorted(channels_dir.glob("channel.*.json")):
        filename = schema_file.name

        # Skip subscribe/unsubscribe - handled by OpenAPI spec
        if filename in {"subscribe.json", "unsubscribe.json"}:
            continue

        # Parse channel info from filename
        channel_name, params = parse_channel_name(filename)
        method_name = to_python_method_name(channel_name)

        # Format channel pattern with placeholders
        channel_pattern = channel_name
        for param in params:
            channel_pattern = channel_pattern.replace(param, f"{{{param}}}")

        # Load schema to extract types
        schema_data = json.loads(schema_file.read_text())
        params_type, notification_type = extract_schema_types(schema_data)

        # Add to imports (only actual schema names, not "dict")
        if params_type != "dict":
            schema_imports.add(params_type)
        if notification_type != "dict":
            schema_imports.add(notification_type)

        # Get description
        description = schema_data.get("description", "")

        channel = ChannelInfo(
            name=method_name,
            channel_pattern=channel_pattern,
            params_type=params_type,
            notification_type=notification_type,
            description=description,
            params=params,
        )

        # Classify as public or private
        if channel_name in PUBLIC_CHANNELS:
            public_channels.append(channel)
        elif channel_name in PRIVATE_CHANNELS:
            private_channels.append(channel)
        else:
            print(f"⚠️  Unknown channel classification: {channel_name}")
            # Default to private for safety
            private_channels.append(channel)

    return public_channels, private_channels, schema_imports


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


def generate_websocket_api(channels_dir: Path, openapi_spec: Path, models_file: Path):
    """Generate WebSocket API file from channel schemas and OpenAPI spec."""

    # Parse generated models to extract result types
    print(f"Parsing generated models: {models_file}")
    source_code = models_file.read_text()
    tree = cst.parse_module(source_code)

    parser = ResponseSchemaParser()
    tree.visit(parser)

    print(f"  Found {len(parser.class_fields)} classes")

    # Parse channels
    public_channels, private_channels, channel_schema_imports = parse_channel_schemas(channels_dir)

    # Parse RPC methods from OpenAPI (using parsed result types)
    public_rpc_methods, private_rpc_methods, rpc_schema_imports = parse_openapi_for_rpc(openapi_spec, parser)

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    env.filters['format_docstring'] = format_docstring

    print("\nGenerating websockets/api.py...")
    template = env.get_template("websocket_api.py.jinja")

    output = template.render(
        public_channels=public_channels,
        private_channels=private_channels,
        public_rpc_methods=public_rpc_methods,
        private_rpc_methods=private_rpc_methods,
        rpc_schema_imports=sorted(rpc_schema_imports),
        channel_schema_imports=sorted(channel_schema_imports),
    )

    output_path = OUTPUT_DIR / "websockets" / "api.py"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output)

    print(f"  → {output_path}")
    print(f"  Public channels: {len(public_channels)}")
    print(f"  Private channels: {len(private_channels)}")
    print(f"  Public RPC methods: {len(public_rpc_methods)}")
    print(f"  Private RPC methods: {len(private_rpc_methods)}")
    print(f"  RPC Schema imports: {len(rpc_schema_imports)}")
    print(f"  Channel Schema imports: {len(channel_schema_imports)}")

    # Show some example result type mappings
    print("\nExample result type mappings:")
    for method in (public_rpc_methods + private_rpc_methods)[:5]:
        print(f"  {method.response_type} → {method.result_type}")


if __name__ == "__main__":
    if not CHANNELS_DIR.exists():
        raise FileNotFoundError(f"Channels directory not found: {CHANNELS_DIR}")
    if not GENERATED_MODELS.exists():
        raise FileNotFoundError(f"Generated models not found: {GENERATED_MODELS}")

    generate_websocket_api(
        channels_dir=CHANNELS_DIR,
        openapi_spec=OPENAPI_SPEC,
        models_file=GENERATED_MODELS,
    )
