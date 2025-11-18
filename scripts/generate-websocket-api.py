import json
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

PACKAGE_DIR = Path(__file__).parent.parent / "derive_client"
CHANNELS_DIR = Path("specs") / "channels"
TEMPLATES_DIR = PACKAGE_DIR / "data" / "templates"
OUTPUT_DIR = PACKAGE_DIR / "_clients"

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
class ChannelInfo:
    name: str  # Python method name
    channel_pattern: str  # e.g., "{subaccount_id}.best.quotes"
    params_type: str  # ChannelParamsSchema
    notification_type: str  # NotificationSchema
    description: str
    params: list[str]  # e.g., ["subaccount_id", "instrument_name"]


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

        # Add to imports
        schema_imports.update([params_type, notification_type])

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


def generate_websocket_api(channels_dir: Path):
    """Generate WebSocket API file from channel schemas."""

    public_channels, private_channels, schema_imports = parse_channel_schemas(channels_dir)

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

    print("Generating websockets/api.py...")
    template = env.get_template("websocket_api.py.jinja")

    output = template.render(
        public_channels=public_channels,
        private_channels=private_channels,
        schema_imports=sorted(schema_imports),
    )

    output_path = OUTPUT_DIR / "websockets" / "api.py"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output)

    print(f"  → {output_path}")
    print(f"  Public channels: {len(public_channels)}")
    print(f"  Private channels: {len(private_channels)}")
    print(f"  Schema imports: {len(schema_imports)}")


if __name__ == "__main__":
    if not CHANNELS_DIR.exists():
        raise FileNotFoundError(f"Channels directory not found: {CHANNELS_DIR}")

    generate_websocket_api(CHANNELS_DIR)
