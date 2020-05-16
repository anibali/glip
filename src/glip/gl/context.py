import weakref
from typing import Optional

import glfw

_glfw_is_initialised = False
def initialise_glfw():
    global _glfw_is_initialised
    if _glfw_is_initialised:
        return
    if not glfw.init():
        raise RuntimeError('Failed to initialise GLFW.')
    glfw.window_hint(glfw.CLIENT_API, glfw.OPENGL_API)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
    _glfw_is_initialised = True


class Window:
    _active: weakref.ReferenceType = lambda: None

    def __init__(
        self,
        width: int,
        height: int,
        title: str = '',
        object_context: Optional['ObjectContext'] = None,
        msaa: int = 1,
        hidden: bool = False,
    ):
        initialise_glfw()
        glfw.window_hint(glfw.SAMPLES, msaa)
        glfw.window_hint(glfw.VISIBLE, not hidden)
        if object_context is None:
            share = None
            object_context = ObjectContext(self)
        else:
            share = object_context._get_glfw_window()
        self._glfw_window = glfw.create_window(width, height, title, None, share)
        if share is not None:
            object_context.attach(self)
        self.object_context = object_context
        self._bound = weakref.WeakValueDictionary()

    def set_bound(self, kind, gl_object):
        assert isinstance(gl_object, kind)
        self._bound[kind] = gl_object

    def get_bound(self, kind):
        return self._bound.get(kind, None)

    def clear_bound(self, kind):
        del self._bound[kind]

    @classmethod
    def get_active(cls) -> Optional['Window']:
        return cls._active()

    def is_active(self):
        return self is Window.get_active()

    def activate(self):
        glfw.make_context_current(self._glfw_window)
        Window._active = weakref.ref(self)

    def destroy(self):
        self.object_context.detach(self)
        glfw.destroy_window(self._glfw_window)
        if self.is_active():
            Window._active = lambda: None
        del self._glfw_window


class ObjectContext:
    def __init__(self, window: Window):
        assert window is not None
        self._windows = weakref.WeakSet([window])

    @staticmethod
    def get_active() -> Optional['ObjectContext']:
        window = Window.get_active()
        if window is None:
            return None
        return window.object_context

    def is_active(self):
        return self is ObjectContext.get_active()

    def attach(self, window: Window):
        self._windows.add(window)

    def detach(self, window: Window):
        self._windows.remove(window)

    def _get_glfw_window(self):
        if len(self._windows) == 0:
            raise RuntimeError('no windows attached to ObjectContext')
        return next(iter(self._windows))._glfw_window
