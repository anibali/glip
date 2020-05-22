"""Adaptation of https://learnopengl.com/Getting-started/Hello-Triangle."""

import numpy as np

import glip

vertex_shader_source = r"""
#version 330 core
layout(location = 0) in vec3 pos;

void main() {
    gl_Position = vec4(pos.x, pos.y, pos.z, 1.0);
}
"""

fragment_shader_source = r"""
#version 330 core
out vec4 FragColor;

void main() {
    FragColor = vec4(1.0f, 0.5f, 0.2f, 1.0f);
}
"""


def main():
    # Enable handy debugging settings.
    glip.cfg.development_mode()

    window = glip.Window(800, 600, 'Hello triangle')
    window.on_resize = lambda width, height: window.set_viewport(0, 0, width, height)

    vertex_shader = glip.VertexShader()
    vertex_shader.compile(vertex_shader_source)
    fragment_shader = glip.FragmentShader()
    fragment_shader.compile(fragment_shader_source)
    program = glip.ShaderProgram()
    program.link([vertex_shader, fragment_shader])
    vertex_shader.destroy()
    fragment_shader.destroy()

    indices = np.asarray([
        0, 1, 3,  # First triangle
        1, 2, 3,  # Second triangle
    ], dtype=np.uint32)

    vertices = np.asarray([
         0.5,  0.5, 0.0,
         0.5, -0.5, 0.0,
        -0.5, -0.5, 0.0,
        -0.5,  0.5, 0.0,
    ], dtype=np.float32)

    ebo = glip.EBO(indices)
    vbo = glip.VBO(vertices)
    # Create a VAO with ebo bound to it.
    vao = glip.VAO(ebo=ebo)

    # Connect vbo data to location 0 (which is `pos` in our vertex shader).
    # TODO: Make a nicer wrapper for this.
    with vao.bound():
        with vbo.bound():
            vbo.gl_vertex_attrib_pointer(0, 3, np.float32, False, 3 * vertices.itemsize, 0)
        vao.gl_enable_vertex_attrib_array(0)

    while not window.should_close():
        # TODO: Process input

        window.clear(colour=[0.2, 0.3, 0.3])

        program.use()
        with vao.bound():
            vao.draw_elements(glip.PrimitiveType.TRIANGLES)

        window.tick()

    # Clean up objects.
    program.destroy()
    vao.destroy()
    vbo.destroy()
    ebo.destroy()
    window.destroy()


if __name__ == '__main__':
    main()
