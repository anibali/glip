import pytest

from glip.gl.context import Window
from glip.config import cfg

cfg.development_mode()


@pytest.fixture
def window():
    window = Window(800, 600, hidden=True)
    window.activate()
    yield window
    window.destroy()
