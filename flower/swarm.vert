#version 120
#extension GL_ARB_explicit_attrib_location : require

uniform sampler2D textex;
uniform sampler2D textex2;

in float id;
in vec2 ids;
out vec4 poscol;
out vec4 velcol;

uniform vec3 dims;
uniform float C;
uniform float R;
uniform vec3 mouse;
uniform float dt;
uniform float rot;

void main()
{
  float c = ids.x;
  float r = ids.y;

  gl_Position = 2*vec4(c,r,0,1) - 1;
  vec4 poses = texture2D( textex, vec2(c,r) );
  vec4 vels = texture2D( textex2, vec2(c,r) );
  
  float x, y, vx, vy, ax, ay, fx, fy, k, q, m;
  x = poses.r;
  y = poses.g;
  vx = vels.r-0.5;
  vy = vels.g-0.5;

  m = (R*C) / (id+1);
  m = min(m,500);

  q = 10*pow(m,0.5);

  float spikes = 4;
  k = 1000*abs(sin(2*3.14*c*spikes));

  fx = 100*(1-r)*cos(c*2*3.14+rot);
  fy = 100*(1-r)*sin(c*2*3.14+rot);
 
//   // Pulsing flower
//   fx *= cos(4*rot);
//   fy *= cos(4*rot);

  // Pulsing galactic trail in square temple?
 fx = 50*clamp(fx, 
   -abs(cos(6*rot)), abs(cos(6*rot)));
 fy = 50*clamp(fy, 
   -abs(cos(6*rot)), abs(cos(6*rot)));

  fx *= mouse.z;
  fy *= mouse.z;

  float dx = mouse.x - x;
  float dy = mouse.y - y;

  ax = (k*dx - q*vx + fx)/m;
  ay = (k*dy - q*vy + fy)/m;

  vx += ax*dt;
  vy += ay*dt;
  x += vx*dt;
  y += vy*dt;

//   // This is not aspect ratio correct...
//   vec2 edge = 0.05*vec2(1,pow(dims.z,3));
//   if( x <   edge.x ){x =   edge.x;}
//   if( x > 1-edge.x ){x = 1-edge.x;}
//   if( y <   edge.y ){y =   edge.y;}
//   if( y > 1-edge.y ){y = 1-edge.y;}

  poscol = vec4( x, y, 0, 1 );
  velcol = vec4( vx+0.5, vy+0.5, 0, 1 );
}