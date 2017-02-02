#version 120
#extension GL_ARB_explicit_attrib_location : require

uniform sampler2D textex;

in float id;
in vec2 ids;
out vec4 poscol;
out vec4 velcol;

uniform vec3 dims;
uniform mat3 cols;
uniform float alpha;
uniform float C;
uniform float R;

void main()
{
  float c = ids.x;
  float r = ids.y;

  poscol = texture2D( textex, vec2(c,r) );
  vec2 pos = 2*poscol.xy-1;
  pos.y *= dims.x/dims.y;

  gl_Position = vec4(pos,id/(R*C),1);

  float m = 1-(id+1)/(R*C);
  poscol = vec4( cols*vec3(r,c,m), alpha );
  
  velcol = vec4(0,0,0,0);
}