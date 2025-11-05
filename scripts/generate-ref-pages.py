"""Generate the code reference pages and navigation."""

from pathlib import Path

import mkdocs_gen_files

REPO_ROOT = Path(__file__).parent.parent
PACKAGE_DIR = REPO_ROOT / "derive_client"


def build_nav_and_files():
    nav = mkdocs_gen_files.Nav()

    public_modules = [
        "derive_client",
        "derive_client.exceptions",
        "derive_client.data_types.enums",
        "derive_client.data_types.models",
    ]

    for module_name in public_modules:
        parts = tuple(module_name.split("."))
        doc_path = Path(*parts).with_suffix(".md")
        full_doc_path = Path("reference", doc_path)

        nav[parts] = doc_path.as_posix()

        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            fd.write(f"# {parts[-1]}\n\n")
            fd.write(f"::: {module_name}\n")
            fd.write("    options:\n")
            fd.write("      show_root_heading: false\n")
            fd.write("      heading_level: 2\n")

    with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
        nav_file.writelines(nav.build_literate_nav())

    # for path in sorted(PACKAGE_DIR.rglob("*.py")):
    #     module_path = path.relative_to(REPO_ROOT).with_suffix("")
    #     doc_path = path.relative_to(REPO_ROOT).with_suffix(".md")
    #     full_doc_path = Path("reference", doc_path)

    #     parts = tuple(module_path.parts)

    #     if parts[-1] == "__init__":
    #         parts = parts[:-1]
    #         doc_path = doc_path.with_name("index.md")
    #         full_doc_path = full_doc_path.with_name("index.md")
    #     elif parts[-1] == "__main__":
    #         continue

    #     nav[parts] = doc_path.as_posix()

    #     with mkdocs_gen_files.open(full_doc_path, "w") as fd:
    #         ident = ".".join(parts)
    #         fd.write(f"::: {ident}")

    #     mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(REPO_ROOT))

    # with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    #     nav_file.writelines(nav.build_literate_nav())


if __name__ == "__main__":
    build_nav_and_files()
