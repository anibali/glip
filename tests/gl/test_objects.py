from glip.gl.objects import VAO, EBO
import numpy as np


def test_ebo(window):
    ebo2 = EBO(np.arange(5, dtype=np.uint32))
    ebo1 = EBO(np.arange(5, dtype=np.uint32))
    vao1 = VAO(ebo1)
    vao2 = VAO(ebo2)
    assert VAO.get_default().is_bound()
    with vao1.bound():
        assert ebo1.is_bound()
        assert vao1.ebo is ebo1
    assert VAO.get_default().is_bound()
    vao2.bind()
    assert ebo2.is_bound()
    assert vao2.ebo is ebo2
    vao2.bind_ebo(ebo1)
    assert ebo1.is_bound()
    assert vao2.ebo is ebo1
    vao1.destroy()
    vao2.destroy()
    ebo1.destroy()
    ebo2.destroy()
