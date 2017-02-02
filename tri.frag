#version 120
#extension GL_ARB_explicit_attrib_location : require

uniform sampler2D textex;
in vec2 coord;
in vec3 colcol;
out vec4 color;

void main()
{
  color = vec4(1,1,1,1);
  if( coord.x >= 0 && coord.y <= 0 ) {
    color = texture2D(textex,coord);
  }
  else { discard; }
  float a = 0.75;
//   color.rgb = a*color.rgb + (1-a)*colcol;
}
