"""
Ensure the project root is on sys.path when pytest sets rootdir to tests/, and
force the 'benchmarking' package to resolve to the real project package instead of
the shadowing tests/benchmarking/ package.

Python automatically imports 'sitecustomize' at startup if it is importable on sys.path.
Placing this file in tests/ guarantees it will be imported first during test collection.
"""

from __future__ import annotations

# Disable third-party plugin autoload (e.g., pytest-asyncio) to rely on our own async shims
# This must be set very early before pytest initializes plugins.
import os as _os_pytest_plugins

_os_pytest_plugins.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

# Early asyncio event loop bootstrap so plugins calling asyncio.get_event_loop() succeed
try:
    import asyncio as _asyncio_boot2
    import sys as _sys_boot2

    if _sys_boot2.platform.startswith("win"):
        try:
            _asyncio_boot2.set_event_loop_policy(_asyncio_boot2.WindowsSelectorEventLoopPolicy())  # type: ignore[attr-defined]
        except Exception:
            pass
    try:
        _asyncio_boot2.get_event_loop()
    except RuntimeError:
        try:
            _loop_boot2 = _asyncio_boot2.new_event_loop()
            _asyncio_boot2.set_event_loop(_loop_boot2)
        except Exception:
            pass
except Exception:
    pass
import importlib.util as _util
import sys
from pathlib import Path

# Compute repository root as the parent of the tests directory
TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
# Prefer src/benchmarking (Phase 2 src layout), fallback to legacy top-level benchmarking/
SRC_BENCH = PROJECT_ROOT / "src" / "benchmarking"
LEGACY_BENCH = PROJECT_ROOT / "benchmarking"
REAL_BENCHMARKING_DIR = SRC_BENCH if SRC_BENCH.exists() else LEGACY_BENCH

# Prepend src/ then project root to sys.path if not already present
SRC_DIR = PROJECT_ROOT / "src"
src_str = str(SRC_DIR)
if src_str not in sys.path:
    sys.path.insert(0, src_str)

project_root_str = str(PROJECT_ROOT)
if project_root_str not in sys.path:
    # Keep PROJECT_ROOT after src to resolve src/ packages like 'fba_events'
    sys.path.insert(1, project_root_str)

# If the real benchmarking package exists, load and bind it explicitly into sys.modules
# to prevent Python from importing the shadow package at tests/benchmarking.
try:
    real_init = REAL_BENCHMARKING_DIR / "__init__.py"
    if REAL_BENCHMARKING_DIR.exists() and real_init.exists():
        spec = _util.spec_from_file_location(
            "benchmarking",
            str(real_init),
            submodule_search_locations=[str(REAL_BENCHMARKING_DIR)],
        )
        if spec and spec.loader:
            mod = _util.module_from_spec(spec)
            # Bind before exec to ensure submodule imports find the correct parent
            sys.modules["benchmarking"] = mod
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            # Ensure correct package path for submodules like benchmarking.metrics
            if not hasattr(mod, "__path__") or not mod.__path__:
                mod.__path__ = [str(REAL_BENCHMARKING_DIR)]  # type: ignore[attr-defined]
except Exception:
    # If anything goes wrong, leave sys.path fix in place; tests will surface issues.
    pass

# Ensure 'integration' resolves to project integration package (avoid collision with tests.integration)
try:
    import importlib.util as _util2
    from pathlib import Path as _Path

    ROOT = _Path(__file__).resolve().parents[1]
    REAL_INTEGRATION_DIR = ROOT / "integration"
    real_init = REAL_INTEGRATION_DIR / "__init__.py"
    if real_init.exists():
        spec2 = _util2.spec_from_file_location(
            "integration",
            str(real_init),
            submodule_search_locations=[str(REAL_INTEGRATION_DIR)],
        )
        if spec2 and spec2.loader:
            imod = _util2.module_from_spec(spec2)
            import sys as _sys

            _sys.modules["integration"] = imod
            spec2.loader.exec_module(imod)  # type: ignore[attr-defined]
            if not hasattr(imod, "__path__") or not imod.__path__:
                imod.__path__ = [str(REAL_INTEGRATION_DIR)]  # type: ignore[attr-defined]
except Exception:
    pass

# Hardening for asyncio event loop access during plugin initialization
# Ensure asyncio.get_event_loop() never fails in MainThread by creating a loop on-demand.
try:
    import asyncio as _aio_patch

    _orig_get_event_loop = _aio_patch.get_event_loop

    def _safe_get_event_loop():
        try:
            return _orig_get_event_loop()
        except RuntimeError:
            # Create and set a new loop for the current thread
            loop = _aio_patch.new_event_loop()
            try:
                _aio_patch.set_event_loop(loop)
            except Exception:
                pass
            return loop

    _aio_patch.get_event_loop = _safe_get_event_loop  # type: ignore[assignment]
except Exception:
    # Best-effort only, never break startup
    pass

# Provide a Safe Event Loop Policy that guarantees a loop exists on get_event_loop()
try:
    import asyncio as _aio_safe

    class _SafeDefaultPolicy(_aio_safe.DefaultEventLoopPolicy):  # type: ignore[attr-defined]
        def get_event_loop(self):
            try:
                return super().get_event_loop()
            except RuntimeError:
                loop = self.new_event_loop()
                try:
                    self.set_event_loop(loop)
                except Exception:
                    pass
                return loop

    # Windows: prefer Selector policy, but make it safe as well
    if hasattr(_aio_safe, "WindowsSelectorEventLoopPolicy"):  # pragma: win32

        class _SafeWindowsSelectorPolicy(_aio_safe.WindowsSelectorEventLoopPolicy):  # type: ignore[attr-defined]
            def get_event_loop(self):
                try:
                    return super().get_event_loop()
                except RuntimeError:
                    loop = self.new_event_loop()
                    try:
                        self.set_event_loop(loop)
                    except Exception:
                        pass
                    return loop

        try:
            _aio_safe.set_event_loop_policy(_SafeWindowsSelectorPolicy())
        except Exception:
            # Fallback to safe default policy
            try:
                _aio_safe.set_event_loop_policy(_SafeDefaultPolicy())
            except Exception:
                pass
    else:
        try:
            _aio_safe.set_event_loop_policy(_SafeDefaultPolicy())
        except Exception:
            pass
except Exception:
    # Non-fatal; tests will still run with default behavior
    pass
