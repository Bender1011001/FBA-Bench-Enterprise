# compat: Auto-mark coroutine tests for pytest-asyncio STRICT mode without touching test files.
import inspect

import pytest


def _is_coroutine_test(item):
    obj = getattr(item, "obj", None)
    if obj is None:
        return False
    # unwrap decorated functions
    while hasattr(obj, "__wrapped__"):
        try:
            obj = obj.__wrapped__
        except Exception:
            break
    return inspect.iscoroutinefunction(obj)


def pytest_collection_modifyitems(session, config, items):
    """
    compat: Ensure async test functions run under pytest-asyncio STRICT mode by
    auto-applying the asyncio marker when the collected test callable is a coroutine function.
    This avoids modifying individual tests or pytest.ini.
    """
    for item in items:
        try:
            # compat: Explicitly mark the standalone dashboard tests as asyncio during collection,
            # even if coroutine detection fails due to decorators or plugin interactions.
            nodeid = getattr(item, "nodeid", "")
            if "tests/test_dashboard_standalone.py" in str(nodeid).replace("\\", "/"):
                if not item.get_closest_marker("asyncio"):
                    item.add_marker(pytest.mark.asyncio)
                # Do not skip remaining logic; allow coroutine-based marking to proceed for consistency.
            # Existing coroutine-based auto-marking for all other tests
            if _is_coroutine_test(item):
                if not item.get_closest_marker("asyncio"):
                    item.add_marker(pytest.mark.asyncio)
        except Exception:
            # Be conservative: never fail collection due to our hook
            continue


def pytest_pyfunc_call(pyfuncitem):
    """
    compat: Fallback executor to run coroutine tests only when async plugins are not active.
    - Gate on pytest-asyncio/anyio presence to avoid clashes.
    - Scope strictly to tests/test_dashboard_standalone.py to avoid impacting other suites.
    - Filter funcargs using function signature to avoid passing extraneous fixtures (e.g., event_loop_policy).
    """
    # Only handle coroutine tests
    try:
        if not _is_coroutine_test(pyfuncitem):
            return None
    except Exception:
        return None

    # Scope fallback strictly to the dashboard standalone suite to prevent clashes elsewhere
    try:
        path_str = str(pyfuncitem.fspath)
        norm_path = path_str.replace("\\", "/")
        if not norm_path.endswith("tests/test_dashboard_standalone.py"):
            return None
    except Exception:
        return None

    # If async test plugins are active, let them handle execution
    import sys

    plugins_active = any(
        mod in sys.modules for mod in ("pytest_asyncio", "pytest_asyncio.plugin", "anyio")
    )

    # compat: If plugins are present, do not run our fallback (avoid double-running)
    if plugins_active:
        return None

    # compat: Even if the item has an asyncio marker, if no plugin is active we still execute the fallback.
    # This prevents "async def functions are not natively supported" errors when plugins are not loaded.

    import asyncio
    import inspect as _inspect

    # compat: Filter kwargs to only declared parameters to avoid extra fixtures like event_loop_policy
    try:
        sig = _inspect.signature(pyfuncitem.obj)
        allowed = set(sig.parameters.keys())
        kwargs = {
            name: pyfuncitem.funcargs[name] for name in allowed if name in pyfuncitem.funcargs
        }
    except Exception:
        kwargs = pyfuncitem.funcargs  # conservative fallback

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        coro = pyfuncitem.obj(**kwargs)
        loop.run_until_complete(coro)
        return True
    finally:
        try:
            # Give pending tasks a chance to finalize cleanly
            loop.run_until_complete(asyncio.sleep(0))
        except Exception:
            pass
        loop.close()
        try:
            asyncio.set_event_loop(None)
        except Exception:
            pass
