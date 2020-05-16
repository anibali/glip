import pytest

from glip.gl.context import Window


@pytest.fixture
def window():
    window = Window(800, 600, hidden=True)
    window.activate()
    return window
