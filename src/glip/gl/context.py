import weakref
from typing import Optional, Callable

import OpenGL.GL as gl
import glfw

from glip.gl.input import Keyboard, Mouse

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
    _active: Optional['Window'] = None
    _default_classes = {}

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
        self._bound = {}
        self.activate()
        self._defaults = {}
        for kind, default_class in self._default_classes.items():
            self._defaults[kind] = default_class()
        # Input
        self.keyboard = Keyboard()
        self.mouse = Mouse()
        # Callbacks
        self.on_resize: Optional[Callable[[int, int], None]] = None
        glfw.set_framebuffer_size_callback(self._glfw_window, self._framebuffer_size_callback)
        glfw.set_key_callback(self._glfw_window, self._key_callback)
        glfw.set_mouse_button_callback(self._glfw_window, self._mouse_button_callback)
        glfw.set_cursor_pos_callback(self._glfw_window, self._cursor_pos_callback)

    def _framebuffer_size_callback(self, glfw_window, width, height):
        if self.on_resize is not None:
            self.on_resize(width, height)

    def _key_callback(self, glfw_window, key, scancode, action, mods):
        self.keyboard.set_modifiers(mods)
        if action == glfw.PRESS:
            self.keyboard.set_key_down(key)
        if action == glfw.RELEASE:
            self.keyboard.set_key_up(key)

    def _mouse_button_callback(self, glfw_window, button, action, mods):
        if action == glfw.PRESS:
            self.mouse.fire_button_down(button, *glfw.get_cursor_pos(self._glfw_window))
        if action == glfw.RELEASE:
            self.mouse.fire_button_up(button, *glfw.get_cursor_pos(self._glfw_window))

    def _cursor_pos_callback(self, glfw_window, x, y):
        self.mouse.fire_move(x, y)

    @classmethod
    def set_bound_default_class(cls, kind, default_class):
        cls._default_classes[kind] = default_class

    @classmethod
    def get_default(cls, kind):
        return cls.get_active()._defaults[kind]

    def set_bound(self, kind, gl_object):
        assert gl_object.kind == kind
        self._bound[kind] = gl_object

    def get_bound(self, kind):
        return self._bound.get(kind, self._defaults.get(kind, None))

    def clear_bound(self, kind):
        if kind in self._bound:
            del self._bound[kind]

    @classmethod
    def get_active(cls) -> Optional['Window']:
        return cls._active

    def is_active(self):
        return self is Window.get_active()

    def activate(self):
        glfw.make_context_current(self._glfw_window)
        Window._active = self

    def destroy(self):
        old_active = Window._active
        self.activate()
        for default in self._defaults.values():
            default.destroy()
        self.object_context.detach(self)
        glfw.destroy_window(self._glfw_window)
        del self._glfw_window
        if old_active is None or old_active is self:
            Window._active = None
        else:
            old_active.activate()

    def clear_colour(self, red: float, green: float, blue: float, alpha: float = 1.0):
        assert self.is_active()
        gl.glClearColor(red, green, blue, alpha)

    def clear(self, colour=None):
        assert self.is_active()
        mask = 0
        if colour is not None:
            if colour is not True:
                self.clear_colour(*colour)
            mask |= gl.GL_COLOR_BUFFER_BIT
        gl.glClear(mask)

    def set_viewport(self, x: int, y: int, width: int, height: int):
        gl.glViewport(x, y, width, height)

    @property
    def should_close(self) -> bool:
        return glfw.window_should_close(self._glfw_window)

    @should_close.setter
    def should_close(self, should_close: bool):
        glfw.set_window_should_close(self._glfw_window, should_close)

    def tick(self):
        glfw.swap_buffers(self._glfw_window)
        glfw.poll_events()
        self.keyboard.update()
        self.mouse.update()


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
