#version 120
#extension GL_ARB_explicit_attrib_location : require

in float c;
in float id;

varying out vec2 coord;
varying out vec3 colcol;

uniform float rot;

void main()
{
  vec2 pos;
  float alpha = 0;
  colcol = vec3(0,0,0);

  if( mod(id,3) == 0 ){ 
    alpha = 2*3.14*(0/3.0);
    coord = vec2(-1,-1);
    colcol.r = 1;
  }
  if( mod(id,3) == 1 ){ 
    alpha = 2*3.14*(1/3.0);
    coord = vec2( 1,-1); 
    colcol.g = 1;
  }
  if( mod(id,3) == 2 ){ 
    alpha = 2*3.14*(2/3.0);
    coord = vec2( 1, 1); 
    colcol.b = 1;
  }
  pos = vec2(cos(alpha),sin(alpha));
  gl_Position = vec4(pos,0.99,1);
}
