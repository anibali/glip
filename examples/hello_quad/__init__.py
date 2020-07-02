"""Adaptation of https://learnopengl.com/Getting-started/Hello-Triangle."""

import numpy as np

import glip

vertex_shader_source = r"""
#version 330 core
in vec3 position;

void main() {
    gl_Position = vec4(position.x, position.y, position.z, 1.0);
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

    window = glip.Window(800, 600, 'Hello quad')
    window.on_resize = lambda width, height: window.set_viewport(0, 0, width, height)

    position_attrib = glip.VertexAttrib(0, size=3, dtype=np.float32)

    program = glip.ShaderProgram(
        vertex_shader=vertex_shader_source,
        fragment_shader=fragment_shader_source,
        vertex_attribs={'position': position_attrib},
    )

    indices = np.asarray([
        0, 1, 3,  # First triangle
        1, 2, 3,  # Second triangle
    ], dtype=np.uint32)

    vertices = np.asarray([
        [+0.5, +0.5, 0.0],
        [+0.5, -0.5, 0.0],
        [-0.5, -0.5, 0.0],
        [-0.5, +0.5, 0.0],
    ], dtype=np.float32)

    ebo = glip.EBO(indices)
    vbo = glip.VBO(vertices)
    # Create a VAO with `ebo` bound to it.
    vao = glip.VAO(ebo=ebo)

    # Connect the position vertex attribute with its data.
    with vao.bound(), vbo.bound():
        vao.connect_vertex_attrib_array(position_attrib, vbo, vertices.strides[0])

    while not window.should_close:
        if window.keyboard.is_down(glip.Key.ESCAPE):
            window.should_close = True

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
