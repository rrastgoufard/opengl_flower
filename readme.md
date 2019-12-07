Flower.py
=========

A cute pyopengl visualization.

Intro
---------

This project is my second attempt at using
pyopengl.  This time around, we do a lot of
stateful computations on the gpu.  Particle
locations and velocities are calculated
in a vertex/fragment shader and saved into 
textures.  Then, each particle is positioned
by reading from those textures and rendered
to the screen using another vertex/fragment
shader.  Ideally we would use some of the
newer opengl features like compute shaders,
but this targeted an older glsl standard that
at the time did not allow me to take that route.

Instructions
-------------

The code is written for python 3.  You will need
numpy, pyopengl, pillow, and poetry.  Pillow's usage
comes when you want to take a screenshot.  
I run linux; not sure if everything works
properly on other operating systems.

To install and run: 
```
python3 -m poetry install
python3 -m poetry shell
python main.py
```

There is only one python script that can be run --
<b>main.py</b>.  It has a few optional 
command line arguments that may be useful.
  * -R int: how many particles per grid row
  * -C int: how many particles per grid column
  * -psize int (1-20): size of each particle
  * -fps int: frame per second cap
  * -w: windowed mode (which can be resized)

If you have a weak gpu, you may want to consider
specifying -R 250 -C 250 instead of the default
-R 500 -C 500.  My surface pro 1 can 
do 250 per row/col at 60 fps, but it cannot
do 500.  Another consideration is to lower the
fps from the default of unconstrained.

Once the program is running, you can interact
with it in a few ways.  The most obvious is 
clicking or dragging using the mouse.  Other
interesting options are with the keys.
  * spacebar: recenter the flower
  * 0: take a screenshot
  * arrow keys: move the flower in large steps
  * r: enable or disable randomly-timed movements
  
There are zero comments in the code, and there
are many too-short variable names.  I never 
intended to make this public, but maybe someone
will see it and get some enjoyment from it.

Hope you have fun!

Videos
--------

Here are videos of it in action!  

Beware the file sizes.  These are download links 
instead of streaming links because streamable 
bitrates compress too much to capture the details.

python flower.py -R 250 -C 250 -psize 2
compressed to crf 30 using libx264 (87MB)
https://drive.google.com/uc?export=download&id=0B_22WXHykI37ZGpGUUt0OVhzS0E

python flower.py -R 500 -C 500 -psize 1
compressed to crf 26 using libx264 (359MB)
https://drive.google.com/uc?export=download&id=0B_22WXHykI37MWgyNkI0M3UzRzQ

Both of these videos are compressed and are
visibly artifacted and less sharp than the
original visualization.  Lots of small dots
flying around is a difficult scenario for any
compression algorithm.
