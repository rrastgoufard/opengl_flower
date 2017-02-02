#version 120
#extension GL_ARB_explicit_attrib_location : require

uniform sampler2D tex1;
uniform vec3 mouse;
in vec2 coord;
out vec4 color;

void main()
{

  float dx = 4.0/1920;
  float dy = 4.0/1080;

  color = texture2D(tex1, coord);
  
  color *= 8;
  color += texture2D(tex1, coord+vec2(dx,dy));
  color += texture2D(tex1, coord+vec2(dx,-dy));
  color += texture2D(tex1, coord+vec2(-dx,dy));
  color += texture2D(tex1, coord+vec2(-dx,-dy));
  color /= 12;
  
  vec2 mouses = vec2(
    (1+cos(mouse.z))/2,
    (1+sin(mouse.z))/2 );
  float distx = pow(mouses.x-coord.x,2); 
  float disty = 1080.0/1920.0*pow(mouses.y-coord.y,2);
  color *= 1-pow(distx+disty,1.0);
  
//   color = 1-color;
//   color = vec4(coord,1,1);
//   color = vec4(1,.5,0,1);
}