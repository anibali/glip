import numpy as np
import pytest

from glip.gl.context import Window
from glip.gl.objects import EBO


def test_shared_object_context():
    window1 = Window(800, 600, hidden=True)
    window2 = Window(800, 600, object_context=window1.object_context, hidden=True)
    window3 = Window(800, 600, hidden=True)
    window1.activate()
    ebo = EBO(np.arange(5, dtype=np.uint32))
    window2.activate()
    ebo.bind()
    window3.activate()
    with pytest.raises(Exception):
        ebo.bind()
    window1.activate()
    ebo.destroy()
    window1.destroy()
    window2.destroy()
    window3.destroy()
