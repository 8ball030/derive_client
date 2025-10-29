"""Generate BridgeClient from AsyncBridgeClient using thin wrappers."""

from pathlib import Path

import libcst as cst
import libcst.matchers as matchers

PACKAGE_DIR = Path(__file__).parent.parent / "derive_client"


class SyncConverter(cst.CSTTransformer):
    """Convert AsyncBridgeClient code to async BridgeClient."""

    def __init__(self):
        super().__init__()
        self.in_try_method = False

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        """Track whether we're inside a try_* method."""
        self.in_try_method = node.name.value.startswith("try_")
        return True

    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef,
    ) -> cst.FunctionDef:
        """Remove async from method definitions."""

        self.in_try_method = False

        # Remove async keyword if present
        if updated_node.asynchronous:
            return updated_node.with_changes(asynchronous=None)
        return updated_node

    def leave_Await(
        self,
        original_node: cst.Await,
        updated_node: cst.Await,
    ) -> cst.BaseExpression:
        """
        Remove await or wrap with run_coroutine_sync.

        - In try_* methods: wrap the awaited expression with run_coroutine_sync()
        - If accessing derive_bridge.light_account: wrap with run_coroutine_sync()
        - In other methods: just remove the await
        """

        if self.in_try_method or self._accesses_derive_bridge_light_account(updated_node.expression):
            # Wrap with run_coroutine_sync(...)
            return cst.Call(
                func=cst.Name("run_coroutine_sync"),
                args=[cst.Arg(value=updated_node.expression)],
            )
        else:
            # Just return the expression without await
            return updated_node.expression

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Add run_coroutine_sync import. We rely on ruff check --fix to fix duplicate import and ordering."""

        # Create the import statement
        run_coroutine_sync_import = cst.SimpleStatementLine(
            body=[
                cst.ImportFrom(
                    module=cst.Attribute(
                        value=cst.Attribute(
                            value=cst.Name("derive_client"),
                            attr=cst.Name("utils"),
                        ),
                        attr=cst.Name("asyncio_sync"),
                    ),
                    names=[cst.ImportAlias(name=cst.Name("run_coroutine_sync"))],
                )
            ],
        )

        # Find the position to insert (after the last import)
        insert_pos = 0
        for i, statement in enumerate(updated_node.body):
            if isinstance(statement, (cst.SimpleStatementLine, cst.Import, cst.ImportFrom)):
                insert_pos = i + 1
            elif isinstance(statement, cst.EmptyLine):
                continue
            else:
                break

        new_body = list(updated_node.body)
        new_body.insert(insert_pos, run_coroutine_sync_import)

        return updated_node.with_changes(body=new_body)

    def leave_ClassDef(
        self,
        original_node: cst.ClassDef,
        updated_node: cst.ClassDef,
    ) -> cst.ClassDef:
        """Rename the class."""
        if updated_node.name.value == "AsyncBridgeClient":
            return updated_node.with_changes(name=cst.Name("BridgeClient"))
        return updated_node

    def _accesses_derive_bridge_light_account(self, node: cst.BaseExpression) -> bool:
        """Check if the expression accesses derive_bridge.light_account."""
        # Match pattern: derive_bridge.light_account.*
        matcher = matchers.Attribute(
            value=matchers.Attribute(
                value=matchers.Name("derive_bridge"),
                attr=matchers.Name("light_account"),
            ),
        )

        # Check if the node itself matches
        if matchers.matches(node, matcher):
            return True

        # If it's a Call, check the func
        if isinstance(node, cst.Call) and matchers.matches(node.func, matcher):
            return True

        # Recursively check if any part of the expression contains the pattern
        if isinstance(node, cst.Call):
            return self._accesses_derive_bridge_light_account(node.func)
        elif isinstance(node, cst.Attribute):
            return self._accesses_derive_bridge_light_account(node.value)

        return False


def generate_sync_bridge_client():
    async_bridge_client = PACKAGE_DIR / "_bridge" / "async_client.py"
    sync_bridge_client = async_bridge_client.parent / "client.py"

    source = async_bridge_client.read_text()
    tree = cst.parse_module(source)
    transformed = tree.visit(SyncConverter())
    sync_bridge_client.write_text(transformed.code)
    print(f"  ✓ Generated {sync_bridge_client}")


if __name__ == "__main__":
    print("Generating sync bridge client...")
    generate_sync_bridge_client()
    print("\n✅ Generation complete!")
