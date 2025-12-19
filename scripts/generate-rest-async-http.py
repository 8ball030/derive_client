"""Generate async versions of sync HTTP clients."""

from pathlib import Path

import libcst as cst
import libcst.matchers as matchers

PACKAGE_DIR = Path(__file__).parent.parent / "derive_client"

# Modules who's methods should be converted to async
ASYNC_OPERATION_MODULES = {
    "account",
    "markets",
    "collateral",
    "orders",
    "positions",
    "transactions",
    "rfq",
    "mmp",
    "trades",
    "rpc",
}

# Methods that should remain synchronous
SYNC_METHODS = {
    "_get_cache_for_type",
    "_get_cached_instrument",
    "sign_action",
}


class AsyncConverter(cst.CSTTransformer):
    """Convert sync client code to async."""

    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef,
    ) -> cst.FunctionDef:
        """Add async to method definitions."""

        if original_node.name.value == "_get_cached_instrument":
            return self._remove_lazy_load_if(updated_node)

        if self._is_cache_property(original_node):
            return self._convert_cache_property(updated_node)

        if not self._should_make_async(original_node):
            return updated_node

        return updated_node.with_changes(asynchronous=cst.Asynchronous(whitespace_after=cst.SimpleWhitespace(" ")))

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call | cst.Await:
        """Add await to function calls."""

        if self._is_api_call(original_node):
            return cst.Await(expression=updated_node)
        return updated_node

    def leave_Name(
        self,
        original_node: cst.Name,
        updated_node: cst.Name,
    ) -> cst.Name:
        """Add async_ prefix to specific utility functions."""

        if updated_node.value == "fetch_all_pages_of_instrument_type":
            return updated_node.with_changes(value="async_fetch_all_pages_of_instrument_type")
        return updated_node

    def leave_ImportFrom(
        self,
        original_node: cst.ImportFrom,
        updated_node: cst.ImportFrom,
    ) -> cst.ImportFrom:
        """Update imports from http to async_http."""

        if original_node.module:
            module_parts = []
            current = original_node.module

            # Traverse the attribute chain to get full module path
            while isinstance(current, cst.Attribute):
                module_parts.insert(0, current.attr.value)
                current = current.value

            if isinstance(current, cst.Name):
                module_parts.insert(0, current.value)

            # Check if this is an import from .http
            if "http" in module_parts and "async_http" not in module_parts:
                # Replace 'http' with 'async_http' in the module path
                new_module_parts = ["async_http" if part == "http" else part for part in module_parts]

                # Reconstruct the module path
                new_module = cst.Name(new_module_parts[0])
                for part in new_module_parts[1:]:
                    new_module = cst.Attribute(value=new_module, attr=cst.Name(part))

                if "api" in module_parts:
                    new_names = []
                    for name in updated_node.names:
                        if isinstance(name, cst.ImportAlias):
                            imported_name = name.name.value if isinstance(name.name, cst.Name) else str(name.name)
                            if imported_name in ("PrivateAPI", "PublicAPI"):
                                new_name = cst.Name(f"Async{imported_name}")
                                new_names.append(name.with_changes(name=new_name))
                            else:
                                new_names.append(name)
                        else:
                            new_names.append(name)

                    return updated_node.with_changes(module=new_module, names=new_names)

                return updated_node.with_changes(module=new_module)

        return updated_node

    def leave_Annotation(
        self,
        original_node: cst.Annotation,
        updated_node: cst.Annotation,
    ) -> cst.Annotation:
        """Update type annotations from PrivateAPI/PublicAPI to Async versions."""

        if isinstance(updated_node.annotation, cst.Name):
            name = updated_node.annotation.value
            if name in ("PrivateAPI", "PublicAPI"):
                new_annotation = cst.Name(f"Async{name}")
                return updated_node.with_changes(annotation=new_annotation)
        return updated_node

    def _should_make_async(self, node: cst.FunctionDef) -> bool:
        """Check if function should be made async."""

        name = node.name.value

        # Skip special methods
        if name.startswith("__") and name.endswith("__"):
            return False

        # Skip explicitly sync methods
        if name in SYNC_METHODS:
            return False

        # Skip properties
        return not self._is_property(node)

    def _is_property(self, node: cst.FunctionDef) -> bool:
        """Check if function is a property decorator."""

        for decorator in node.decorators:
            if matchers.matches(decorator, matchers.Decorator(decorator=matchers.Name("property"))):
                return True
        return False

    def _is_cache_property(self, node: cst.FunctionDef) -> bool:
        """Check if this is a cache property (erc20/perp/option_instruments_cache)."""

        name = node.name.value
        return self._is_property(node) and name.endswith("_instruments_cache")

    def _convert_cache_property(self, node: cst.FunctionDef) -> cst.FunctionDef:
        """Convert cache property to raise error if cache is empty instead of lazy loading."""

        statements = node.body.body

        if_index = next((i for i, stmt in enumerate(statements) if isinstance(stmt, cst.If)), None)
        if if_index is None:
            raise ValueError(f"Could not find expected if-statement in {node.name.value} function body: ")

        if_stmt = statements[if_index]
        err_msg = f"Call fetch_instruments() or fetch_all_instruments() to create the {node.name.value}."
        raise_exc = cst.Call(
            func=cst.Name("RuntimeError"),
            args=[cst.Arg(value=cst.SimpleString(f'"{err_msg}"'))],
        )
        raise_stmt = cst.Raise(exc=raise_exc)

        new_if_body = cst.IndentedBlock(body=[cst.SimpleStatementLine(body=[raise_stmt])])
        new_if = if_stmt.with_changes(body=new_if_body)

        new_statements = list(statements[:if_index]) + [new_if] + list(statements[if_index + 1 :])
        new_body = node.body.with_changes(body=new_statements)

        return node.with_changes(body=new_body)

    def _is_api_call(self, node: cst.Call) -> bool:
        """Check if this call should be awaited."""

        # Pattern 1: <anything>.<module>.<method>(...)
        if isinstance(node.func, cst.Attribute):
            method_name = node.func.attr.value

            # Check if calling a method on one of our operation modules
            if isinstance(node.func.value, cst.Attribute):
                module_name = node.func.value.attr.value
                if module_name in ASYNC_OPERATION_MODULES and method_name not in SYNC_METHODS:
                    return True

            # Pattern 2: <var>.<method>(...) where method is a known async method
            # This handles self.get_ticker(), client.fetch_subaccounts(), etc.
            if isinstance(node.func.value, cst.Name) and method_name not in SYNC_METHODS:
                var_name = node.func.value.value
                if var_name == "self":
                    return True

        # Pattern 3: <var>.<method>(...) where var is an API instance
        if isinstance(node.func, cst.Attribute) and isinstance(node.func.value, cst.Name):
            var_name = node.func.value.value
            if var_name in ("private_api", "public_api"):
                return True

        # utility function: fetch_all_pages_of_instrument_type
        if isinstance(node.func, cst.Name):
            func_name = node.func.value
            if func_name.startswith("fetch_"):
                return True

        return False

    def _remove_lazy_load_if(self, node: cst.FunctionDef) -> cst.FunctionDef:
        """
        Remove the `if not cache: cache = await self.fetch_instruments(...)` block.

        Looks for a top-level `If` whose test is `not cache` and removes that statement.
        Returns the original node unchanged if not found (safe).
        """

        statements = node.body.body

        # find an If with `not cache`
        def is_not_cache_if(stmt: cst.BaseSmallStatement) -> bool:
            if not isinstance(stmt, cst.If):
                return False
            test = stmt.test
            if isinstance(test, cst.UnaryOperation) and isinstance(test.operator, cst.Not):
                expr = test.expression
                return isinstance(expr, cst.Name) and expr.value == "cache"
            return False

        if_index = next((i for i, s in enumerate(statements) if is_not_cache_if(s)), None)
        if if_index is None:
            return node

        # remove that If statement
        new_statements = [*statements[:if_index], *statements[if_index + 1 :]]

        new_body = node.body.with_changes(body=new_statements)
        return node.with_changes(body=new_body)


class AsyncTestConverter(cst.CSTTransformer):
    """Convert sync test code to async."""

    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef,
    ) -> cst.FunctionDef:
        """Add async to test functions and add pytest.mark.asyncio decorator."""

        if self._should_skip(original_node):
            return updated_node

        # Make function async
        async_func = updated_node.with_changes(
            asynchronous=cst.Asynchronous(whitespace_after=cst.SimpleWhitespace(" "))
        )

        # Add @pytest.mark.asyncio decorator to test functions
        if original_node.name.value.startswith("test_"):
            decorator = cst.Decorator(
                decorator=cst.Attribute(
                    value=cst.Attribute(
                        value=cst.Name("pytest"),
                        attr=cst.Name("mark"),
                    ),
                    attr=cst.Name("asyncio"),
                )
            )
            existing_decorators = list(async_func.decorators)
            new_decorators = existing_decorators + [decorator]
            async_func = async_func.with_changes(decorators=new_decorators)

        return async_func

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call | cst.Await:
        """Add await to client method calls and helper functions."""

        if self._is_client_call(original_node) or self._is_helper_call(original_node):
            return cst.Await(expression=updated_node)
        return updated_node

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Add pytest import. We rely on ruff check --fix to fix duplicate import and ordering."""

        # Add pytest import at the top (after any existing imports)
        pytest_import = cst.SimpleStatementLine(
            body=[cst.Import(names=[cst.ImportAlias(name=cst.Name("pytest"))])],
            trailing_whitespace=cst.TrailingWhitespace(
                whitespace=cst.SimpleWhitespace(""),
                newline=cst.Newline(),
            ),
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
        new_body.insert(insert_pos, pytest_import)

        return updated_node.with_changes(body=new_body)

    def leave_ImportFrom(
        self,
        original_node: cst.ImportFrom,
        updated_node: cst.ImportFrom,
    ) -> cst.ImportFrom:
        """Update imports from http to async_http."""

        if original_node.module:
            module_parts = []
            current = original_node.module

            # Traverse the attribute chain to get full module path
            while isinstance(current, cst.Attribute):
                module_parts.insert(0, current.attr.value)
                current = current.value

            if isinstance(current, cst.Name):
                module_parts.insert(0, current.value)

            # Check if this is an import from .http
            if "http" in module_parts and "async_http" not in module_parts:
                # Replace 'http' with 'async_http' in the module path
                new_module_parts = ["async_http" if part == "http" else part for part in module_parts]

                # Reconstruct the module path
                new_module = cst.Name(new_module_parts[0])
                for part in new_module_parts[1:]:
                    new_module = cst.Attribute(value=new_module, attr=cst.Name(part))

                if "api" in module_parts:
                    new_names = []
                    for name in updated_node.names:
                        if isinstance(name, cst.ImportAlias):
                            imported_name = name.name.value if isinstance(name.name, cst.Name) else str(name.name)
                            if imported_name in ("PrivateAPI", "PublicAPI"):
                                new_name = cst.Name(f"Async{imported_name}")
                                new_names.append(name.with_changes(name=new_name))
                            else:
                                new_names.append(name)
                        else:
                            new_names.append(name)

                    return updated_node.with_changes(module=new_module, names=new_names)

                return updated_node.with_changes(module=new_module)

        return updated_node

    def _should_skip(self, node: cst.FunctionDef) -> bool:
        """Check if function should not be made async."""

        return bool(node.name.value.startswith("__"))

    def _is_client_call(self, node: cst.Call) -> bool:
        """Check if this is a client method call that needs await."""

        # Pattern: <anything>.<module>.<method>(...)
        # Pattern 1: <anything>.<module>.<method>(...) - existing
        if isinstance(node.func, cst.Attribute) and isinstance(node.func.value, cst.Attribute):
            module_name = node.func.value.attr.value
            if module_name in ASYNC_OPERATION_MODULES:
                method_name = node.func.attr.value
                if method_name not in SYNC_METHODS:
                    return True

        # Pattern 2: <var_name>.<method>(...)
        # For direct client methods like client.fetch_subaccounts()
        if isinstance(node.func, cst.Attribute) and isinstance(node.func.value, cst.Name):
            method_name = node.func.attr.value
            if method_name.startswith("fetch_"):
                return True
        return False

    def _is_helper_call(self, node: cst.Call) -> bool:
        """Check if this is a helper function call that needs await."""

        # Pattern: _create_order(...) or other helper functions
        return bool(isinstance(node.func, cst.Name) and node.func.value.startswith("_"))


def generate_async_client():
    source_dir = PACKAGE_DIR / "_clients" / "rest" / "http"
    target_dir = source_dir.parent / "async_http"

    excluded = ["session.py", "client.py", "api.py", "__init__.py"]

    for py_file in source_dir.glob("*.py"):
        if py_file.name in excluded:
            continue

        source = py_file.read_text()
        tree = cst.parse_module(source)
        transformed = tree.visit(AsyncConverter())

        target_file = target_dir / py_file.name
        target_file.write_text(transformed.code)
        print(f"  ✓ Generated {target_file}")


def generate_async_tests():
    source_dir = PACKAGE_DIR.parent / "tests" / "test_clients" / "test_rest" / "test_http"
    target_dir = source_dir.parent / "test_async_http"

    excluded = ["conftest.py", "__init__.py"]

    for py_file in source_dir.glob("*.py"):
        if py_file.name in excluded:
            continue

        source = py_file.read_text()
        tree = cst.parse_module(source)
        transformed = tree.visit(AsyncTestConverter())

        target_file = target_dir / py_file.name
        target_file.write_text(transformed.code)
        print(f"  ✓ Generated {target_file}")


if __name__ == "__main__":
    print("Generating async clients...")
    generate_async_client()
    print("\nGenerating async tests...")
    generate_async_tests()
    print("\n✅ Generation complete!")
