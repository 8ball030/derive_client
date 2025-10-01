import json
import re
from pathlib import Path

import requests
from datamodel_code_generator import DataModelType, InputFileType, PythonVersion, generate
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TIMEOUT = 10


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


def download_openapi_specs(base_url: str, dest_dir: Path) -> list[Path]:
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
        output_model_type=DataModelType.DataclassesDataclass,
        target_python_version=PythonVersion.PY_310,
        reuse_model=True,
        use_subclass_enum=True,
        strict_nullable=True,
        use_double_quotes=True,
        field_constraints=True,
    )
    print(f"Models generated at: {output_path}")


if __name__ == "__main__":
    base_url = "https://docs.derive.xyz"
    repo_root = Path(__file__).parent.parent

    openapi_specs_path = repo_root / "derive_client" / "data" / "openapi"
    openapi_specs_path.mkdir(exist_ok=True)

    files = download_openapi_specs(base_url=base_url, dest_dir=openapi_specs_path)

    input_path = next((p for p in files if "latest" in p.stem.lower()), None)
    if input_path is None:
        available = ", ".join(p.name for p in files)
        raise RuntimeError(f"No 'latest' spec found among downloaded files: {available}")

    output_path = repo_root / "derive_client" / "_clients" / "models.py"
    generate_models(input_path=input_path, output_path=output_path)
