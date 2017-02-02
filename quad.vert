#version 120
#extension GL_ARB_explicit_attrib_location : require

// pos.xy is the texture location from (0,0) to (1,1)
// pos.zw is the position from (-1,-1) to (1,1)
in vec4 pos;
out vec2 coord;

void main()
{
  gl_Position = vec4(pos.zw,0,1);
  coord = pos.xy;
}