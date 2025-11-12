"""Generate INTERNAL API reference (for contributors/advanced users)."""

from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

REPO_ROOT = Path(__file__).parent.parent
PACKAGE_DIR = REPO_ROOT / "derive_client"

for path in sorted(PACKAGE_DIR.rglob("*.py")):
    module_path = path.relative_to(REPO_ROOT).with_suffix("")
    doc_path = path.relative_to(REPO_ROOT).with_suffix(".md")
    full_doc_path = Path("internal", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        continue

    if "tests" in parts or "generated" in parts:
        continue

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}\n")
        fd.write("    options:\n")
        fd.write("      show_root_heading: true\n")

    mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(REPO_ROOT))

with mkdocs_gen_files.open("internal/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
