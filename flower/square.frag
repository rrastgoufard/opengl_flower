#version 120
#extension GL_ARB_explicit_attrib_location : require

in vec4 poscol;
in vec4 velcol;
layout (location = 0) out vec4 cpos;
layout (location = 1) out vec4 cvel;

void main()
{
  cpos = poscol;
  cvel = velcol;
}