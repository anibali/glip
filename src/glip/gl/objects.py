import traceback
import warnings
from abc import ABC, abstractmethod

import OpenGL.GL as gl

from glip.config import cfg
from glip.gl.context import Window


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
    def __init__(self, kind, handle, shareable):
        super().__init__(handle, shareable)
        self._kind = kind

    @abstractmethod
    def _do_bind(self):
        pass

    def is_bound(self):
        """Returns True if this object is bound to the current OpenGL context."""
        return self is Window.get_active().get_bound(self._kind)

    def bind(self):
        if not self.is_bound():
            self._do_bind()
            Window.get_active().set_bound(self._kind, self)

    def destroy(self):
        super().destroy()
        if self._shareable:
            windows = self._window.object_context._windows
        else:
            windows = [self._window]
        for window in windows:
            if self is window.get_bound(self._kind):
                window.clear_bound(self._kind)


class BufferObject(_BindableGLObject):
    def __init__(self, kind, target):
        self._target = target
        super().__init__(kind, gl.glGenBuffers(1), shareable=True)
        self.bind()

    def _do_bind(self):
        gl.glBindBuffer(self._target, self.handle)

    def _do_destroy(self):
        if gl.glDeleteBuffers is not None:
            gl.glDeleteBuffers(1, [self.handle])


class VBO(BufferObject):
    def __init__(self):
        super().__init__(VBO, gl.GL_ARRAY_BUFFER)


class EBO(BufferObject):
    def __init__(self):
        super().__init__(EBO, gl.GL_ELEMENT_ARRAY_BUFFER)


class UBO(BufferObject):
    def __init__(self):
        super().__init__(UBO, gl.GL_UNIFORM_BUFFER)


class VAO(_BindableGLObject):
    def __init__(self):
        super().__init__(VAO, gl.glGenVertexArrays(1), shareable=False)

    def _do_bind(self):
        gl.glBindVertexArray(self.handle)

    def _do_destroy(self):
        if gl.glDeleteVertexArrays is not None:
            gl.glDeleteVertexArrays(1, [self.handle])


class TextureObject(_BindableGLObject):
    def __init__(self, kind, target):
        self._target = target
        super().__init__(kind, gl.glGenTextures(1), shareable=True)
        self.bind()

    def _do_bind(self):
        gl.glBindTexture(self._target, self.handle)

    def _do_destroy(self):
        if gl.glDeleteTextures is not None:
            gl.glDeleteTextures(1, [self.handle])


class Texture2D(TextureObject):
    def __init__(self):
        super().__init__(Texture2D, gl.GL_TEXTURE_2D)


class ShaderObject(_GLObject):
    def __init__(self, shader_type):
        self._shader_type = shader_type
        super().__init__(gl.glCreateShader(shader_type), shareable=True)

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
    def __init__(self):
        super().__init__(gl.GL_VERTEX_SHADER)


class FragmentShader(ShaderObject):
    def __init__(self):
        super().__init__(gl.GL_FRAGMENT_SHADER)


class ShaderProgram(_BindableGLObject):
    def __init__(self):
        super().__init__(ShaderProgram, gl.glCreateProgram(), shareable=True)

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

    def _do_bind(self):
        gl.glUseProgram(self.handle)

    def _do_destroy(self):
        if gl.glDeleteProgram is not None:
            gl.glDeleteProgram(self.handle)
