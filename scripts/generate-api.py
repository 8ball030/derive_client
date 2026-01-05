"""Unified API generation script for REST and WebSocket clients"""

import json
import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import libcst as cst
from jinja2 import Environment, FileSystemLoader

# Paths
PACKAGE_DIR = Path(__file__).parent.parent / "derive_client"
OPENAPI_SPEC = PACKAGE_DIR.parent / "specs" / "openapi-spec.json"
CHANNELS_DIR = Path("specs") / "channels"
TEMPLATES_DIR = PACKAGE_DIR / "data" / "templates"
OUTPUT_DIR = PACKAGE_DIR / "_clients"
GENERATED_MODELS_PATH = PACKAGE_DIR / "data_types" / "generated_models.py"
CHANNEL_MODELS_DIR = PACKAGE_DIR / "data_types" / "channels"

# Channel classifications from docs
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
class ParamInfo:
    name: str
    type_annotation: str
    is_enum: bool = False


@dataclass
class ChannelInfo:
    name: str  # Python method name
    channel_pattern: str  # e.g., "{subaccount_id}.best.quotes"
    params_type: str  # ChannelParamsSchema
    notification_type: str  # NotificationSchema
    notification_data_type: str = "Any"  # Actual data payload type
    description: str = ""
    params: list[ParamInfo] = field(default_factory=list)


class ResponseSchemaParser(cst.CSTVisitor):
    """Parse generated_models.py to extract actual result field types from ResponseSchema classes."""

    def __init__(self):
        self.result_types: dict[str, str] = {}
        self.class_bases: dict[str, list[str]] = {}
        self.class_fields: dict[str, dict[str, str]] = {}
        self.current_class: Optional[str] = None

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        class_name = node.name.value
        self.current_class = class_name
        self.class_fields.setdefault(class_name, {})

        bases = []
        for base in node.bases:
            try:
                base_name = self._annotation_to_string(base.value)
            except Exception:
                base_name = ""
            base_name = base_name.split("[", 1)[0].strip()
            if base_name:
                if "." in base_name:
                    base_name = base_name.rsplit(".", 1)[-1]
                bases.append(base_name)
        self.class_bases[class_name] = bases

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        self.current_class = None

    def visit_AnnAssign(self, node: cst.AnnAssign) -> None:
        if not self.current_class:
            return

        target = node.target
        field_name = target.value if isinstance(target, cst.Name) else self._annotation_to_string(target)

        annotation_node = getattr(node, "annotation", None)
        if not annotation_node:
            return

        annot_expr = annotation_node.annotation
        field_type = self._annotation_to_string(annot_expr).strip()

        if (field_type.startswith("'") and field_type.endswith("'")) or (
            field_type.startswith('"') and field_type.endswith('"')
        ):
            field_type = field_type[1:-1]

        self.class_fields.setdefault(self.current_class, {})[field_name] = field_type

    def _annotation_to_string(self, node: cst.BaseExpression) -> str:
        try:
            text = cst.Module([]).code_for_node(node)
            return text.strip()
        except Exception:
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


class ChannelModelParser(cst.CSTVisitor):
    """Parse generated channel model files to extract schema and enum types."""

    def __init__(self):
        self.schemas: dict[str, dict[str, str]] = {}  # class_name -> {field_name: type}
        self.enums: set[str] = set()
        self.current_class: Optional[str] = None
        self.current_file_enums: set[str] = set()  # Track enums in current file

    def visit_Module(self, node: cst.Module) -> None:
        """Reset file-level enum tracking for each module."""
        self.current_file_enums = set()

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        class_name = node.name.value
        self.current_class = class_name

        # Check if it's an Enum
        for base in node.bases:
            try:
                base_name = self._annotation_to_string(base.value)
                if "Enum" in base_name:
                    self.enums.add(class_name)
                    self.current_file_enums.add(class_name)
                    return
            except Exception:
                continue

        # It's a Struct schema
        self.schemas.setdefault(class_name, {})

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        self.current_class = None

    def visit_AnnAssign(self, node: cst.AnnAssign) -> None:
        if not self.current_class or self.current_class in self.enums:
            return

        target = node.target
        field_name = target.value if isinstance(target, cst.Name) else self._annotation_to_string(target)

        annotation_node = getattr(node, "annotation", None)
        if not annotation_node:
            return

        annot_expr = annotation_node.annotation
        field_type = self._annotation_to_string(annot_expr).strip()

        if (field_type.startswith("'") and field_type.endswith("'")) or (
            field_type.startswith('"') and field_type.endswith('"')
        ):
            field_type = field_type[1:-1]

        self.schemas[self.current_class][field_name] = field_type

    def _annotation_to_string(self, node: cst.BaseExpression) -> str:
        try:
            text = cst.Module([]).code_for_node(node)
            return text.strip()
        except Exception:
            return repr(node)


def parse_channel_models(channels_dir: Path) -> tuple[dict[str, dict[str, str]], set[str]]:
    """Parse all generated channel model files to extract schemas and enums."""

    parser = ChannelModelParser()

    # Parse public channel models
    public_dir = channels_dir / "public"
    if public_dir.exists():
        for model_file in public_dir.glob("*.py"):
            if model_file.name == "__init__.py":
                continue
            try:
                source = model_file.read_text()
                tree = cst.parse_module(source)
                tree.visit(parser)
            except Exception as e:
                print(f"  ⚠️  Error parsing {model_file}: {e}")

    # Parse private channel models
    private_dir = channels_dir / "private"
    if private_dir.exists():
        for model_file in private_dir.glob("*.py"):
            if model_file.name == "__init__.py":
                continue
            try:
                source = model_file.read_text()
                tree = cst.parse_module(source)
                tree.visit(parser)
            except Exception as e:
                print(f"  ⚠️  Error parsing {model_file}: {e}")

    return parser.schemas, parser.enums


def extract_schema_names_from_type(type_annotation: str) -> set[str]:
    """Extract actual schema class names from type annotation, filtering out generics and builtins."""

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

    pattern = r'\b([A-Z][a-zA-Z0-9_]*)\b'
    matches = re.findall(pattern, type_annotation)

    schema_names = set()
    for match in matches:
        if match not in GENERICS and match not in BUILTINS:
            schema_names.add(match)

    return schema_names


def parse_openapi_for_rpc(spec_path: Path, parser: ResponseSchemaParser):
    """Parse OpenAPI spec for RPC methods."""

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
        result_type = parser.get_result_type(response_type)
        description = post_spec["description"]

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


def parse_channel_name(filename: str) -> tuple[str, list[str]]:
    """Parse channel filename to extract channel pattern and parameters."""

    name = filename.replace("channel.", "").replace(".json", "")
    params = []
    parts = name.split(".")

    param_patterns = {
        "subaccount_id",
        "instrument_name",
        "instrument_type",
        "currency",
        "group",
        "depth",
        "interval",
        "tx_status",
    }

    for part in parts:
        if part in param_patterns:
            params.append(part)

    return name, params


def to_python_method_name(channel_name: str) -> str:
    """Convert channel name to Python method name with disambiguation."""

    parts = channel_name.split(".")
    param_indicators = {"instrument_name", "instrument_type", "currency", "subaccount_id", "wallet"}

    method_parts = []
    found_params = []

    for part in parts:
        if part in param_indicators:
            found_params.append(part)
        else:
            method_parts.append(part)

    base_name = "_".join(method_parts)

    if found_params:
        suffix = f"by_{found_params[0]}"
        return f"{base_name}_{suffix}"

    return base_name


def extract_schema_types(schema_data: dict) -> tuple[str, str]:
    """Extract channel params and notification schema types from JSON schema."""

    definitions = schema_data.get("definitions", {})

    pubsub_schema = None
    for name, defn in definitions.items():
        if "PubSubSchema" in name:
            pubsub_schema = defn
            break

    if not pubsub_schema:
        return "dict", "dict"

    props = pubsub_schema.get("properties", {})

    params_ref = props.get("channel_params", {}).get("$ref", "")
    params_type = params_ref.split("/")[-1] if params_ref else "dict"

    notification_ref = props.get("notification", {}).get("$ref", "")
    notification_type = notification_ref.split("/")[-1] if notification_ref else "dict"

    return params_type, notification_type


def get_notification_data_type(
    notification_schema_name: str,
    channel_schemas: dict[str, dict[str, str]],
) -> str:
    """Extract the actual data type from notification.params.data path."""

    # Navigate: NotificationSchema -> params field -> NotificationParamsSchema -> data field
    if notification_schema_name not in channel_schemas:
        return "Any"

    # Get the params field type from NotificationSchema
    notification_fields = channel_schemas[notification_schema_name]
    params_type = notification_fields.get("params", "")

    if not params_type or params_type not in channel_schemas:
        return "Any"

    # Get the data field type from NotificationParamsSchema
    params_fields = channel_schemas[params_type]
    data_type = params_fields.get("data", "")

    if not data_type:
        return "Any"

    return data_type


def get_param_type_annotation(
    param_name: str, params_schema_name: str, channel_schemas: dict[str, dict[str, str]], channel_enums: set[str]
) -> tuple[str, bool]:
    """Get the type annotation for a channel parameter from the generated schema.

    Returns:
        tuple: (type_annotation, is_enum)
    """

    # Check if we have a schema for the params
    if params_schema_name in channel_schemas:
        param_fields = channel_schemas[params_schema_name]
        if param_name in param_fields:
            type_str = param_fields[param_name]

            # Extract all type names from the annotation (handles Optional, Union, etc.)
            type_names = extract_schema_names_from_type(type_str)

            # Check if any of the types is an enum
            for type_name in type_names:
                if type_name in channel_enums:
                    # Return the actual type annotation with the enum
                    return type_str, True

            # Not an enum
            return type_str, False

    # Fallback to str for unknown types
    return "str", False


def collect_all_channel_imports(
    params_type: str,
    notification_type: str,
    params: list[ParamInfo],
    notification_data_type: str,
    channel_schemas: dict[str, dict[str, str]],
    channel_enums: set[str],
) -> set[str]:
    """Collect all necessary imports for a channel, including nested types."""

    imports = set()

    # Add the main schemas
    if params_type != "dict":
        imports.add(params_type)

    if notification_type != "dict":
        imports.add(notification_type)

    # Add the notification params schema (intermediate type)
    if notification_type in channel_schemas:
        params_field = channel_schemas[notification_type].get("params", "")
        if params_field and params_field != "dict":
            imports.add(params_field)

    # Add the actual data type from notification
    if notification_data_type != "Any":
        imports.update(extract_schema_names_from_type(notification_data_type))

    # Add enum types from parameters
    for param in params:
        param_types = extract_schema_names_from_type(param.type_annotation)
        # Add all extracted types (this includes enums)
        imports.update(param_types)

    return imports


def parse_channel_schemas(channels_dir: Path, channel_schemas: dict[str, dict[str, str]], channel_enums: set[str]):
    """Parse all channel JSON schemas."""

    public_channels = []
    private_channels = []
    schema_imports = set()

    for schema_file in sorted(channels_dir.glob("channel.*.json")):
        filename = schema_file.name

        if filename in {"subscribe.json", "unsubscribe.json"}:
            continue

        channel_name, param_names = parse_channel_name(filename)
        method_name = to_python_method_name(channel_name)

        channel_pattern = channel_name
        for param in param_names:
            channel_pattern = channel_pattern.replace(param, f"{{{param}}}")

        schema_data = json.loads(schema_file.read_text())
        params_type, notification_type = extract_schema_types(schema_data)

        # Build params list with proper type annotations
        params = []
        for param_name in param_names:
            type_annotation, is_enum = get_param_type_annotation(
                param_name, params_type, channel_schemas, channel_enums
            )
            params.append(ParamInfo(name=param_name, type_annotation=type_annotation, is_enum=is_enum))

        # Get the actual notification data type
        notification_data_type = get_notification_data_type(notification_type, channel_schemas)

        # Collect all imports for this channel
        channel_imports = collect_all_channel_imports(
            params_type,
            notification_type,
            params,
            notification_data_type,
            channel_schemas,
            channel_enums,
        )
        schema_imports.update(channel_imports)

        description = schema_data.get("description", "")

        channel = ChannelInfo(
            name=method_name,
            channel_pattern=channel_pattern,
            params_type=params_type,
            notification_type=notification_type,
            notification_data_type=notification_data_type,
            description=description,
            params=params,
        )

        if channel_name in PUBLIC_CHANNELS:
            public_channels.append(channel)
        elif channel_name in PRIVATE_CHANNELS:
            private_channels.append(channel)
        else:
            print(f"⚠️  Unknown channel classification: {channel_name}")
            private_channels.append(channel)

    return public_channels, private_channels, schema_imports


def format_docstring(text: str, width: int = 88) -> str:
    """Format text as a proper Python docstring."""

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


def generate_api_file(
    template_name: str,
    output_path: Path,
    public_methods: list[MethodInfo],
    private_methods: list[MethodInfo],
    rpc_schema_imports: set[str],
    is_async: bool = False,
    api_prefix: str = "",
    client_type: str = "http",
    public_channels: list[ChannelInfo] = None,
    private_channels: list[ChannelInfo] = None,
    channel_schema_imports: set[str] = None,
):
    """Generate a single API file from unified template."""

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    env.filters['format_docstring'] = format_docstring

    template = env.get_template(template_name)

    output = template.render(
        public_rpc_methods=public_methods,
        private_rpc_methods=private_methods,
        rpc_schema_imports=sorted(rpc_schema_imports),
        is_async=is_async,
        api_prefix=api_prefix,
        client_type=client_type,
        public_channels=public_channels or [],
        private_channels=private_channels or [],
        channel_schema_imports=sorted(channel_schema_imports or set()),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output)


def generate_all_files():
    """Generate all API files (REST and WebSocket) from unified template."""

    # Parse generated models
    print("Parsing generated_models.py...")
    if not GENERATED_MODELS_PATH.exists():
        raise FileNotFoundError(f"Generated models not found at {GENERATED_MODELS_PATH}")

    source_code = GENERATED_MODELS_PATH.read_text()
    tree = cst.parse_module(source_code)
    parser = ResponseSchemaParser()
    tree.visit(parser)
    print(f"  → Found {len(parser.class_fields)} classes")

    # Parse OpenAPI spec
    print("\nParsing OpenAPI spec...")
    public_methods, private_methods, rpc_schema_imports = parse_openapi_for_rpc(OPENAPI_SPEC, parser)
    print(f"  → {len(public_methods)} public methods")
    print(f"  → {len(private_methods)} private methods")
    print(f"  → {len(rpc_schema_imports)} RPC schema imports")

    # Generate REST endpoints
    print("\nGenerating endpoints.py...")
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("endpoints.py.jinja")
    output = template.render(
        public_methods=public_methods,
        private_methods=private_methods,
    )
    endpoints_path = OUTPUT_DIR / "rest" / "endpoints.py"
    endpoints_path.write_text(output)
    print(f"  → {endpoints_path}")

    # Generate REST HTTP API (sync)
    print("\nGenerating rest/http/api.py...")
    generate_api_file(
        template_name="api.py.jinja",
        output_path=OUTPUT_DIR / "rest" / "http" / "api.py",
        public_methods=public_methods,
        private_methods=private_methods,
        rpc_schema_imports=rpc_schema_imports,
        is_async=False,
        api_prefix="",
        client_type="http",
    )

    # Generate REST HTTP API (async)
    print("Generating rest/async_http/api.py...")
    generate_api_file(
        template_name="api.py.jinja",
        output_path=OUTPUT_DIR / "rest" / "async_http" / "api.py",
        public_methods=public_methods,
        private_methods=private_methods,
        rpc_schema_imports=rpc_schema_imports,
        is_async=True,
        api_prefix="Async",
        client_type="http",
    )

    # Parse channels for WebSocket
    if CHANNELS_DIR.exists():
        print("\nParsing channel model files...")
        channel_schemas, channel_enums = parse_channel_models(CHANNEL_MODELS_DIR)
        print(f"  → Found {len(channel_schemas)} channel schemas")
        print(f"  → Found {len(channel_enums)} channel enums")

        print("\nParsing channel schemas...")
        public_channels, private_channels, channel_schema_imports = parse_channel_schemas(
            CHANNELS_DIR, channel_schemas, channel_enums
        )
        print(f"  → {len(public_channels)} public channels")
        print(f"  → {len(private_channels)} private channels")
        print(f"  → {len(channel_schema_imports)} channel schema imports")

        # Generate WebSocket API
        print("\nGenerating websockets/api.py...")
        generate_api_file(
            template_name="api.py.jinja",
            output_path=OUTPUT_DIR / "websockets" / "api.py",
            public_methods=public_methods,
            private_methods=private_methods,
            rpc_schema_imports=rpc_schema_imports,
            is_async=False,
            api_prefix="",
            client_type="websocket",
            public_channels=public_channels,
            private_channels=private_channels,
            channel_schema_imports=channel_schema_imports,
        )
    else:
        print(f"\n⚠️  Channels directory not found: {CHANNELS_DIR}")
        print("  Skipping WebSocket generation")

    print("\n✓ All API generation complete!")


if __name__ == "__main__":
    if not OPENAPI_SPEC.exists():
        raise FileNotFoundError(f"OpenAPI spec not found at {OPENAPI_SPEC}")

    generate_all_files()
