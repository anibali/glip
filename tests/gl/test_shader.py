from glip.gl.objects import ShaderProgram, VertexShader, FragmentShader


vertex_shader_source = r"""
#version 330 core
in vec3 pos;

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


def test_shader(window):
    vertex_shader = VertexShader()
    vertex_shader.compile(vertex_shader_source)
    fragment_shader = FragmentShader()
    fragment_shader.compile(fragment_shader_source)
    program = ShaderProgram()
    program.link([vertex_shader, fragment_shader])
    program.use()
