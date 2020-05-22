import ctypes as C
import enum
import sys
import traceback
import warnings
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Optional

import OpenGL.GL as gl
import numpy as np

from glip.config import cfg
from glip.gl.context import Window


def np_to_gl_type(np_type: np.dtype):
    if np_type == np.int8:
        return gl.GL_BYTE
    if np_type == np.uint8:
        return gl.GL_UNSIGNED_BYTE
    if np_type == np.int16:
        return gl.GL_SHORT
    if np_type == np.uint16:
        return gl.GL_UNSIGNED_SHORT
    if np_type == np.int32:
        return gl.GL_INT
    if np_type == np.uint32:
        return gl.GL_UNSIGNED_INT
    if np_type == np.float16:
        return gl.GL_HALF_FLOAT
    if np_type == np.float32:
        return gl.GL_FLOAT
    if np_type == np.float64:
        return gl.GL_DOUBLE
    raise TypeError(f'Unsupported base data type: {np_type}')


class PrimitiveType(enum.Enum):
    POINTS = gl.GL_POINTS
    LINES = gl.GL_LINES
    LINE_LOOP = gl.GL_LINE_LOOP
    LINE_STRIP = gl.GL_LINE_STRIP
    TRIANGLES = gl.GL_TRIANGLES
    TRIANGLE_STRIP = gl.GL_TRIANGLE_STRIP
    TRIANGLE_FAN = gl.GL_TRIANGLE_FAN
    LINES_ADJACENCY = gl.GL_LINES_ADJACENCY
    LINE_STRIP_ADJACENCY = gl.GL_LINE_STRIP_ADJACENCY
    TRIANGLES_ADJACENCY = gl.GL_TRIANGLES_ADJACENCY
    TRIANGLE_STRIP_ADJACENCY = gl.GL_TRIANGLE_STRIP_ADJACENCY
    PATCHES = gl.GL_PATCHES


class _GLObject(ABC):
    def __init__(self, handle, shareable):
        self._handle = handle
        window = Window.get_active()
        assert window is not None
        self._window = window
        self._shareable = shareable
        if cfg.monitor_leaks:
            self._stack_trace = traceback.StackSummary.extract(traceback.walk_stack(None))

    @property
    def handle(self):
        """Get the OpenGL handle for this object."""
        assert self.exists_in_current_context()
        assert not self.is_destroyed()
        return self._handle

    def exists_in_current_context(self):
        """Returns True if this object exists in the current OpenGL context."""
        if self._shareable:
            return self._window.object_context.is_active()
        return self._window.is_active()

    def is_destroyed(self):
        return self._handle is None

    @abstractmethod
    def _do_destroy(self):
        pass

    def destroy(self):
        self._do_destroy()
        self._handle = None

    def __del__(self):
        if cfg.monitor_leaks and not self.is_destroyed():
            warnings.warn('A GL object has been garbage collected without being destroyed first.\n'
                          'Stack trace for object creation:\n'
                          + ''.join(self._stack_trace.format()[1:]))


class _BindableGLObject(_GLObject):
    def __init__(self, handle, shareable):
        super().__init__(handle, shareable)

    @property
    @classmethod
    @abstractmethod
    def kind(cls) -> str:
        pass

    @classmethod
    def get_bound(cls):
        return Window.get_active().get_bound(cls.kind)

    def _set_bound(self):
        Window.get_active().set_bound(self.kind, self)

    @classmethod
    @abstractmethod
    def _do_bind(cls, handle):
        pass

    def is_bound(self):
        """Returns True if this object is bound to the current OpenGL context."""
        assert self.exists_in_current_context()
        return self is self.get_bound()

    def bind(self) -> bool:
        if self.is_bound():
            return False
        self._do_bind(self.handle)
        self._set_bound()
        return True

    @classmethod
    def unbind(cls):
        cls._do_bind(0)
        Window.get_active().clear_bound(cls.kind)

    @contextmanager
    def bound(self):
        if self.is_bound():
            yield self
        else:
            prev_bound = self.get_bound()
            self.bind()
            yield self
            if prev_bound is None:
                self.unbind()
            else:
                prev_bound.bind()

    @classmethod
    @contextmanager
    def unbound(cls):
        prev_bound = cls.get_bound()
        cls.unbind()
        yield cls.get_bound()
        if prev_bound is None:
            cls.unbind()
        else:
            prev_bound.bind()

    def destroy(self):
        super().destroy()
        if self._shareable:
            windows = self._window.object_context._windows
        else:
            windows = [self._window]
        for window in windows:
            if self is window.get_bound(self.kind):
                window.clear_bound(self.kind)


class BufferObject(_BindableGLObject):
    @property
    @classmethod
    @abstractmethod
    def _target(cls) -> str:
        pass

    def __init__(self):
        super().__init__(gl.glGenBuffers(1), shareable=True)

    @classmethod
    def _do_bind(cls, handle):
        gl.glBindBuffer(cls._target, handle)

    def _do_destroy(self):
        if gl.glDeleteBuffers is not None:
            gl.glDeleteBuffers(1, [self.handle])


class VBO(BufferObject):
    kind = object()
    _target = gl.GL_ARRAY_BUFFER

    def __init__(self, data: Optional[np.ndarray] = None, usage=gl.GL_DYNAMIC_DRAW):
        super().__init__()
        self.usage = usage
        if data is not None:
            with self.bound():
                self.allocate_and_write(data)

    def allocate_and_write(self, data: np.ndarray):
        assert self.is_bound()
        gl.glBufferData(gl.GL_ARRAY_BUFFER, data.nbytes, data.data, self.usage)

    def gl_vertex_attrib_pointer(self, index, size, np_type, normalised: bool, stride: int, offset: int):
        assert self.is_bound()
        gl.glVertexAttribPointer(index, size, np_to_gl_type(np_type), normalised, stride, C.c_void_p(offset))


class EBO(BufferObject):
    kind = object()
    _target = gl.GL_ELEMENT_ARRAY_BUFFER

    def __init__(self, data: np.ndarray, usage=gl.GL_DYNAMIC_DRAW):
        super().__init__()
        self.usage = usage
        self._length = len(data)
        self._gl_type = np_to_gl_type(data.dtype.base)
        with self.bound():
            self.allocate_and_write(data)

    def bind(self) -> bool:
        changed = super().bind()
        if changed:
            vao = VAO.get_bound()
            vao._ebo = self
        return changed

    def allocate_and_write(self, data: np.ndarray):
        assert self.is_bound()
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, data.nbytes, data.data, self.usage)

    def draw_elements(self, mode: PrimitiveType = PrimitiveType.TRIANGLES):
        assert self.is_bound()
        gl.glDrawElements(mode.value, self._length, self._gl_type, None)


class UBO(BufferObject):
    kind = object()
    _target = gl.GL_UNIFORM_BUFFER


class _VAO(_BindableGLObject):
    kind = object()

    def __init__(self, handle):
        super().__init__(handle, shareable=False)
        self._ebo = None

    def bind(self) -> bool:
        changed = super().bind()
        if changed:
            if self.ebo is not None:
                self.ebo._set_bound()
            else:
                Window.get_active().clear_bound(EBO.kind)
        return changed

    def bind_ebo(self, ebo: EBO):
        assert self.is_bound()
        ebo.bind()

    @property
    def ebo(self):
        return self._ebo

    def draw_elements(self, mode: PrimitiveType = PrimitiveType.TRIANGLES):
        assert self.is_bound()
        assert self.ebo is not None
        self.ebo.draw_elements(mode)

    def gl_enable_vertex_attrib_array(self, index):
        assert self.is_bound()
        gl.glEnableVertexAttribArray(index)

    @classmethod
    def _do_bind(cls, handle):
        gl.glBindVertexArray(handle)


class DefaultVAO(_VAO):
    def __init__(self):
        super().__init__(0)

    def _do_destroy(self):
        pass


class VAO(_VAO):
    def __init__(self, ebo: Optional[EBO] = None):
        super().__init__(gl.glGenVertexArrays(1))
        if ebo is not None:
            with self.bound():
                self.bind_ebo(ebo)

    @classmethod
    def get_default(cls):
        return Window.get_default(cls.kind)

    def _do_destroy(self):
        if gl.glDeleteVertexArrays is not None:
            gl.glDeleteVertexArrays(1, [self.handle])


class TextureObject(_BindableGLObject):
    @property
    @classmethod
    @abstractmethod
    def _target(cls) -> str:
        pass

    def __init__(self):
        super().__init__(gl.glGenTextures(1), shareable=True)

    @classmethod
    def _do_bind(cls, handle):
        gl.glBindTexture(cls._target, handle)

    def _do_destroy(self):
        if gl.glDeleteTextures is not None:
            gl.glDeleteTextures(1, [self.handle])


class Texture2D(TextureObject):
    kind = object()
    _target = gl.GL_TEXTURE_2D


class ShaderObject(_GLObject):
    @property
    @classmethod
    @abstractmethod
    def _shader_type(cls) -> str:
        pass

    def __init__(self):
        super().__init__(gl.glCreateShader(self._shader_type), shareable=True)

    def gl_shader_source(self, source):
        gl.glShaderSource(self.handle, source)

    def gl_compile_shader(self):
        gl.glCompileShader(self.handle)

    def gl_get_shader_iv(self, pname):
        return gl.glGetShaderiv(self.handle, pname)

    def gl_get_shader_info_log(self):
        return gl.glGetShaderInfoLog(self.handle).decode()

    def compile(self, source, check_errors=True):
        self.gl_shader_source(source)
        self.gl_compile_shader()
        if check_errors:
            if not self.gl_get_shader_iv(gl.GL_COMPILE_STATUS):
                error = self.gl_get_shader_info_log()
                raise RuntimeError(f'Shader compilation failed: {error}')

    def _do_destroy(self):
        if gl.glDeleteShader is not None:
            gl.glDeleteShader(self.handle)


class VertexShader(ShaderObject):
    _shader_type = gl.GL_VERTEX_SHADER


class FragmentShader(ShaderObject):
    _shader_type = gl.GL_FRAGMENT_SHADER


class ShaderProgram(_BindableGLObject):
    kind = object()

    def __init__(self):
        super().__init__(gl.glCreateProgram(), shareable=True)

    def gl_attach_shader(self, shader: ShaderObject):
        gl.glAttachShader(self.handle, shader.handle)

    def gl_detach_shader(self, shader: ShaderObject):
        gl.glDetachShader(self.handle, shader.handle)

    def gl_link_program(self):
        gl.glLinkProgram(self.handle)

    def gl_get_program_iv(self, pname):
        return gl.glGetProgramiv(self.handle, pname)

    def gl_get_program_info_log(self):
        return gl.glGetProgramInfoLog(self.handle).decode()

    def link(self, shaders, check_errors=True):
        # Attach the shaders to this program.
        for shader in shaders:
            self.gl_attach_shader(shader)
        # Link the shader program.
        self.gl_link_program()
        # Check for linking errors.
        if check_errors:
            if not self.gl_get_program_iv(gl.GL_LINK_STATUS):
                error = self.gl_get_program_info_log()
                raise RuntimeError(f'Shader linking failed: {error}')
        # Detach shaders so that it's possible to free shader source and unlinked object code.
        for shader in shaders:
            self.gl_detach_shader(shader)

    def use(self):
        self.bind()

    @classmethod
    def _do_bind(cls, handle):
        gl.glUseProgram(handle)

    def _do_destroy(self):
        if gl.glDeleteProgram is not None:
            gl.glDeleteProgram(self.handle)


# Add a hook for unhandled exceptions which disables warnings for leak monitoring.
old_excepthook = sys.excepthook
def excepthook(*args):
    cfg.monitor_leaks = False
    old_excepthook(*args)
sys.excepthook = excepthook


Window.set_bound_default_class(VAO.kind, DefaultVAO)
