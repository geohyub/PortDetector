"""PortDetector Desktop smoke test — offscreen PySide6 윈도우 생성 확인."""

import sys
import os
import pytest

# Path setup
_ROOT = os.path.join(os.path.dirname(__file__), "..")
_SHARED = os.path.join(_ROOT, "..", "..", "_shared")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _SHARED)

os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture(scope="module")
def app():
    from PySide6.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication(sys.argv)
    yield _app


def test_main_window_creates(app):
    """MainWindow가 offscreen에서 정상 생성되는지 확인."""
    from desktop.main_window import MainWindow
    window = MainWindow()
    assert window is not None


def test_py_compile():
    """desktop/ 하위 모든 .py 파일이 py_compile 통과하는지 확인."""
    import py_compile
    desktop_dir = os.path.join(_ROOT, "desktop")
    errors = []
    for root, _, files in os.walk(desktop_dir):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                try:
                    py_compile.compile(path, doraise=True)
                except py_compile.PyCompileError as e:
                    errors.append(str(e))
    assert not errors, f"py_compile 실패:\n" + "\n".join(errors)
