from __future__ import print_function
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import sys
import os
import time
import thread
import threading
import itertools as IT

import argparse

import numpy as np
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("-fps", type=float)
parser.add_argument("-R", type=int)
parser.add_argument("-C", type=int)
parser.add_argument("-v", action="store_true")
parser.add_argument("-w", action="store_false")
parser.add_argument("-psize", type=int)
args = parser.parse_args()

def imread( filename ):
  im = Image.open( filename )
  imout = np.array( im, dtype="f" ) / 255.0
  return imout

def linearim( im ):
  w,h,d = im.shape
  imout = np.zeros( (w*h*d), dtype=im.dtype )
  for i in range(d):
    imout[i::d] = np.hstack( im[:,:,i] )
  return imout

class Context():
  
  kiosk = False
  printstatus = args.v
  fullscreen = args.w
  printfps = False
  rendertotexture = False

  W, H = (600, 400)
  mousex = 0
  mousey = 0
  
  mousehoverx = 0
  mousehovery = 0
  
  mousedown = False
  randommode = True
  
  #R = 1024/4
  #C = 1024/4
  R = args.R if args.R else 500
  C = args.C if args.C else 500
  
  psize = args.psize if args.psize else 1
  lsize = 1
  points = True
  
  fpsr = args.fps if args.fps else -75.0
  sleeptime = 0.0
  
  # for the background color
  randfreqs = np.random.random( 3 )
  randmod = 3
  
  RenderTargets = {}
  NRenderTargets = [
    (0,C,R),
    (1,C,R),
    (2,None,None)
  ]
  renderstatus = 0 # this will flip between 0 
                   # and 1 to serve as ping pong.
  
  def get_time(self):
    return np.float64(time.time()) - self.tstart
  
  def game_time(self):
    return self.get_time() - self.tpaused

  def __init__(self):
    glutInit()
    glutInitDisplayMode(
      GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA )
    glutInitWindowSize(self.W, self.H)
    glutInitWindowPosition(50, 30)
    window = glutCreateWindow("Bubbles")
    
    self.loadShaders()
    self.initBuffers()
    self.loadRenderTargets()
    
    self.initData()
    
    glutDisplayFunc(self.Render)
    glutIdleFunc(self.Render)
    glutReshapeFunc(self.ResizeGL)
    
    glutKeyboardFunc(self.keyPressed)
    glutKeyboardUpFunc(self.keyReleased)
    glutSpecialFunc(self.keyPressed)
    glutMouseFunc(self.mouseFunc)
    glutMotionFunc(self.mouseMotion)
    glutPassiveMotionFunc(self.mousePassive)
    
    self.initMouse()
    self.tpaused = 0
    self.tstart = time.time()
    self.t = self.get_time()
    self.tg = self.t
    self.last_window = self.W, self.H
    if self.fullscreen:
      glutFullScreen()
    print( "{} rows, {} cols, {} total".format(
      self.R, self.C, self.R*self.C ) )
    glutMainLoop()

  def loadRenderTargets(self):
    for i,W,H in self.NRenderTargets:
      W = self.W if not W else W
      H = self.H if not H else H
      if not i in self.RenderTargets:
        fb = glGenFramebuffers(1)
        tex = glGenTextures(1)
        tex2 = glGenTextures(1)
        dep = glGenRenderbuffers(1)
        fbdict = {
          "framebuffer" : fb,
          "texture" : tex,
          "texture2" : tex2,
          "depthbuffer" : dep,
          "width" : W,
          "height" : H
        }
        self.RenderTargets[i] = fbdict
      else:
        fb = self.RenderTargets[i]["framebuffer"]
        tex = self.RenderTargets[i]["texture"]
        tex2 = self.RenderTargets[i]["texture2"]
        dep = self.RenderTargets[i]["depthbuffer"]
        self.RenderTargets[i]["width"] = W
        self.RenderTargets[i]["height"] = H
      
      glBindFramebuffer(GL_FRAMEBUFFER,fb)
      
      glActiveTexture(GL_TEXTURE0 + tex)
      glBindTexture(GL_TEXTURE_2D, tex)
      glTexImage2D( 
        GL_TEXTURE_2D,    # target
        0,                # level?
        GL_RGBA32F,           # internal format
        W,                # width
        H,                # height
        0,                # border
        GL_RGBA,           # format (not internal?)
        GL_UNSIGNED_BYTE, # type
        None )            # null pointer
      # Disable interpolation so that the pixels
      # look correct.  (Is that the reason?)
      interp = GL_NEAREST
      glTexParameteri( 
        GL_TEXTURE_2D, 
        GL_TEXTURE_MAG_FILTER, 
        interp )
      glTexParameteri( 
        GL_TEXTURE_2D, 
        GL_TEXTURE_MIN_FILTER, 
        interp )
      
      glActiveTexture(GL_TEXTURE0 + tex2)
      glBindTexture(GL_TEXTURE_2D, tex2)
      glTexImage2D( 
        GL_TEXTURE_2D,    # target
        0,                # level?
        GL_RGBA32F,           # internal format
        W,                # width
        H,                # height
        0,                # border
        GL_RGBA,           # format (not internal?)
        GL_UNSIGNED_BYTE, # type
        None )            # null pointer
      # Disable interpolation so that the pixels
      # look correct.  (Is that the reason?)
      interp = GL_NEAREST
      glTexParameteri( 
        GL_TEXTURE_2D, 
        GL_TEXTURE_MAG_FILTER, 
        interp )
      glTexParameteri( 
        GL_TEXTURE_2D, 
        GL_TEXTURE_MIN_FILTER, 
        interp )      
      
      glBindRenderbuffer( GL_RENDERBUFFER,dep)
      glRenderbufferStorage( GL_RENDERBUFFER,
        GL_DEPTH_COMPONENT, W, H )
      glFramebufferRenderbuffer( GL_FRAMEBUFFER,
        GL_DEPTH_ATTACHMENT,
        GL_RENDERBUFFER,
        dep )

      # Configure the framebuffer
      glFramebufferTexture2D( 
        GL_FRAMEBUFFER,
        GL_COLOR_ATTACHMENT0,
        GL_TEXTURE_2D,
        tex, 
        0 )
      glFramebufferTexture2D( 
        GL_FRAMEBUFFER,
        GL_COLOR_ATTACHMENT1,
        GL_TEXTURE_2D,
        tex2, 
        0 )      
      glDrawBuffers( 2, [GL_COLOR_ATTACHMENT0,
                         GL_COLOR_ATTACHMENT1] )
      
      glBindFramebuffer(GL_FRAMEBUFFER,fb)
      glClearColor(0.5,0.5,0.5,0.5)
      glClear( GL_DEPTH_BUFFER_BIT | 
               GL_COLOR_BUFFER_BIT )
      
      if self.printstatus:
        fstring = "RenderTarget {i}, {w}x{h}"
        fstring += ", fb:{fb}, dep:{dep}"
        fstring += ", tex:{tex}, tex2:{tex2}"
        print( fstring.format(
          i = i, w = W, h = H,
          fb = fb, dep = dep, 
          tex = tex, tex2 = tex2 ) )
  
  def loadShaders(self):
    self.programs = {}
    self.shaders = {}
    progs = [ 
      ("tri", [
        ("tri.vert",
          GL_VERTEX_SHADER),
        ("tri.frag", 
          GL_FRAGMENT_SHADER)
        ] ),
      ("square", [
        ("square.vert",
          GL_VERTEX_SHADER),
        ("square.frag",
          GL_FRAGMENT_SHADER)
        ] ),
      ("swarm", [
        ("swarm.vert",
          GL_VERTEX_SHADER),
        ("square.frag",
          GL_FRAGMENT_SHADER)
        ] ),
      ("quad", [
        ("quad.vert",
          GL_VERTEX_SHADER),
        ("quad.frag",
          GL_FRAGMENT_SHADER)
        ] ),
        
    ]
        
    def gimme_program(shads, ext=""):
      program = glCreateProgram()
      shaders = {}
      for f, shadertype in shads:
        fext = f.split(".")
        fext[-2] += ext
        fext = ".".join(fext)
        #print(fext)
        
        with open(fext, "r") as fin:
          fstring = fin.read()
          shaders[f] = glCreateShader( 
            shadertype )
          glShaderSource(shaders[f], fstring)
          glCompileShader(shaders[f])
          #print(f)
          s = glGetShaderInfoLog(shaders[f])
          #if s:
            #print(s)
          glAttachShader(program, shaders[f])
      glLinkProgram(program)
      s = glGetProgramInfoLog(program)
      if s:
        #print("Linker Messages!")
        #print(s)
        raise EnvironmentError
      return shaders, program

    try:
      for p, shads in progs:
        shaders, program = gimme_program(shads)
        self.programs[p] = program  
    except EnvironmentError as e:
      for p, shads in progs:
        shaders, program = gimme_program(shads,
                                         ext="_nv")
        self.programs[p] = program
    
  def initBuffers(self):
    self.buffers = {}
    self.attribs = {}
    self.arrays = {}
    self.textures = {}
    
    keys = [
      ("tri", "c", GL_FLOAT, 3, 1),
      ("tri", "id", GL_FLOAT, 3, 1),
      ("tri", "textex", GL_INT),
      ("tri", "rot", GL_FLOAT),
      
      ("quad", "pos", GL_FLOAT, 4, 4),
      ("quad", "tex1", GL_INT),
      ("quad", "mouse", GL_FLOAT),

      ("square", "id", GL_FLOAT,
        self.R*self.C, 1),
      ("square", "ids", GL_FLOAT,
        self.R*self.C, 2),
      ("square", "textex", GL_INT),
      ("square", "dims", GL_FLOAT),
      ("square", "cols", GL_FLOAT),
      ("square", "alpha", GL_FLOAT),
      ("square", "R", GL_FLOAT),
      ("square", "C", GL_FLOAT),
      
      ("swarm", "id", GL_FLOAT,
        self.R*self.C, 1),
      ("swarm", "ids", GL_FLOAT,
        self.R*self.C, 2),      
      ("swarm", "textex", GL_INT),
      ("swarm", "textex2", GL_INT),
      ("swarm", "dims", GL_FLOAT),
      ("swarm", "R", GL_FLOAT),
      ("swarm", "C", GL_FLOAT),
      ("swarm", "mouse", GL_FLOAT),
      ("swarm", "dt", GL_FLOAT),
      ("swarm", "rot", GL_FLOAT)
    ]
    for widekey in keys:
      if len(widekey) == 5:
        prog, name, glt, N, stride = widekey
        uniform = False
      else:
        prog, name, glt = widekey
        uniform = True
      key = (prog, name)
      if self.printstatus:
        print(key, glt)
      if not prog in self.arrays:
        vao = glGenVertexArrays(1)
        self.arrays[prog] = vao
      vao = self.arrays[prog]
      glBindVertexArray( vao )
      if self.printstatus:
        print("  vao: {}".format(vao))
      
      if not key in self.buffers and not uniform:
        vbo = glGenBuffers(1)
        vertices = np.ones(N*stride, "float32")
        glBindBuffer(
          GL_ARRAY_BUFFER, 
          vbo )
        glBufferData(
          GL_ARRAY_BUFFER,
          vertices,
          GL_STREAM_DRAW )
        self.buffers[key] = vbo
        if self.printstatus:
          print( "  buffer: {}".format(vbo) )
      if not key in self.attribs and not uniform:
        attrib = glGetAttribLocation(
          self.programs[prog], name )
        if self.printstatus:
          print("  attrib: {}".format(attrib))
        if attrib >= 0:
          glVertexAttribPointer(
            attrib,
            stride,
            glt,
            GL_FALSE,
            0,
            None )
          glEnableVertexAttribArray( attrib )
        self.attribs[key] = attrib
      if not key in self.attribs and uniform:
        attrib = glGetUniformLocation(
          self.programs[prog], name )
        self.attribs[key] = attrib
        if self.printstatus:
          print("  uniform: {}".format(attrib))
        
  def loadTexture(self, key, imname):
    if not key in self.textures:
      self.textures[key] = glGenTextures( 1 )
    if self.printstatus:
      print( "texture {}: {}".format(
        key, self.textures[key] ) )
    glActiveTexture( 
      GL_TEXTURE0 + self.textures[key] )
    glBindTexture( GL_TEXTURE_2D, 
      self.textures[key] )
    interp = GL_LINEAR
    glTexParameteri( GL_TEXTURE_2D, 
      GL_TEXTURE_MIN_FILTER, interp )
    glTexParameteri( GL_TEXTURE_2D, 
      GL_TEXTURE_MAG_FILTER, interp )
    glTexParameteri( GL_TEXTURE_2D, 
      GL_TEXTURE_WRAP_S, GL_REPEAT )
    glTexParameteri( GL_TEXTURE_2D, 
      GL_TEXTURE_WRAP_T, GL_REPEAT )
    
    im = imread( imname )
    w,h,_ = im.shape
    pixels = linearim( im )
    if self.printstatus:
      print( "{} by {}".format(w,h) )
    
    glTexImage2D(
      GL_TEXTURE_2D,
      0,
      GL_RGB,
      w,
      h,
      0,
      GL_RGB,
      GL_FLOAT,
      pixels )
    
  def loadData(self, key, data):
    glBindBuffer(GL_ARRAY_BUFFER, 
                 self.buffers[key])
    glBufferData( 
      GL_ARRAY_BUFFER,
      data,
      GL_STREAM_DRAW )
    
  def initData(self):
    key = ("square", "id")
    d = np.arange(self.R*self.C)
    d = np.array(d,"float32")
    self.loadData(key,d)
    
    x = np.linspace(0,self.C-1,self.C)
    y = np.linspace(0,self.R-1,self.R)
    x = (x+0.5)/self.C
    y = (y+0.5)/self.R
    xx,yy = np.meshgrid(x,y)
    xx = np.reshape( xx, [-1, 1] )
    yy = np.reshape( yy, [-1, 1] )
    d = np.hstack( [xx, yy] )
    d = np.array(d,"float32")
    
    key = ("swarm", "ids")
    self.loadData(key,d)
    
    key = ("square", "ids")
    self.loadData(key,d)
    
    #xx = np.array([0,1,0,1])
    #yy = np.array([0,0,1,1])
    #d = np.hstack([xx,yy,2*xx-1,2*yy-1])
    #d = 0.5*np.array(d,"float32")
    d = np.array( [
      [0,0,-1,-1],
      [1,0,1,-1],
      [0,1,-1,1],
      [1,1,1,1]
      ], "float32" )
    key = ("quad", "pos")
    self.loadData(key,d)
    
  def keyPressed(self, key, *args):
    if self.kiosk:
      return
    if self.printstatus:
      print( "key! '{}' {}".format(key,args))
    if key == '\x1b':
      sys.exit(0)    
    elif key == '0':
      self.writePNG()
      if self.printstatus:
        for RTi in self.RenderTargets:
          RT = self.RenderTargets[RTi]
          self.getTex( tex=RT["texture"],
            name="rt{}_texture1".format(RTi) )
          self.getTex( tex=RT["texture2"],
            name="rt{}_texture2".format(RTi) )
    elif key == 's':
      self.printstatus = not self.printstatus
    elif key == ' ':
      self.initMouse()
    elif key == 'c':
      self.transitionColors()
    elif key == 'r':
      self.randommode = True
    elif key == 't':
      self.rendertotexture = not self.rendertotexture
    elif key == 'p':
      self.points = not self.points
    elif key == GLUT_KEY_UP:
      self.mousey -= 0.25*self.H
      self.mousey = np.clip(self.mousey,0,self.H)
    elif key == GLUT_KEY_DOWN:
      self.mousey += 0.25*self.H
      self.mousey = np.clip(self.mousey,0,self.H)      
    elif key == GLUT_KEY_LEFT:
      self.mousex -= 0.25*self.W
      self.mousex = np.clip(self.mousex,0,self.W)
    elif key == GLUT_KEY_RIGHT:
      self.mousex += 0.25*self.W
      self.mousex = np.clip(self.mousex,0,self.W)

  def keyReleased(self, *args):
    pass
    
  def mouseFunc(self, *args):
    if self.kiosk:
      return
    if len(args) == 4:
      self.mousex, self.mousey = args[2:]
      if args[:2] == (3,0):
        self.psize += 1
      if args[:2] == (4,0):
        self.psize -= 1
      self.psize = np.clip(self.psize,1,20)
      if args[1] == 0:
        self.mousedown = True
        self.randommode = False
      if args[1] == 1:
        self.mousedown = False
      if self.printstatus:
        print(args)
    
  def mouseMotion(self, x, y):
    if self.kiosk:
      return
    self.mousex, self.mousey = x, y
    if x > 0.98*self.W and y < 0.02*self.H:
      sys.exit(0)
    
  def mousePassive(self, *args):
    self.mousehoverx, self.mousehovery = args
    
  def reshapeFunc(self, *args):
    pass
  
  def updateTime(self):
    self.told = self.t
    self.tgold = self.tg
    self.t = self.get_time()
    self.tg = self.game_time()
    self.rendertime = self.t - self.told
    self.rendertimeg = self.tg - self.tgold
    if self.fpsr > 0:
      self.sleeptime += 0.1*(
        1.0/self.fpsr - self.rendertime )
      if self.sleeptime > 0:
        time.sleep( self.sleeptime )
        
    if self.tg - self.randmod > self.rendertime:
      a = 10
      if self.tg - self.randmod > 2*self.rendertime:
        self.randmod += np.random.randint(4,10)
        self.transitionColors()
        a = 0.6
      if self.randommode:
        if self.printstatus:
          print("Random mouse at",self.tg)
        b = (1-a)/2
        rs = a*np.random.random(2) + b
        self.mousex = self.W*rs[0]
        self.mousey = self.H*rs[1]
        
  def Render( self, *args ):
    self.updateTime()
    if self.printfps:
      print( "{:>2.2f} fps".format(
        1/self.rendertime))
    
    glViewport(0, 0, self.W, self.H)
    if self.rendertotexture:
      RT = self.RenderTargets[2]
      glBindFramebuffer(GL_FRAMEBUFFER,
                        RT["framebuffer"])    
    else:
      glBindFramebuffer(GL_FRAMEBUFFER,0)
    self.drawBackground()

    if self.printstatus:
      glViewport(self.W*3/4,self.H*3/4,
                 self.W/4,self.H/4)
      self.drawTri(
        tex=self.RenderTargets[
          self.renderstatus]["texture"])
      glViewport(self.W*3/4,self.H*2/4,
                 self.W/4,self.H/4)
      self.drawTri(
        tex=self.RenderTargets[
          self.renderstatus]["texture2"])

    glViewport(0, 0, self.W, self.H)
    self.drawSquares()
    self.drawSwarm()
    
    if self.rendertotexture:
      glViewport(0, 0, self.W, self.H)
      glBindFramebuffer(GL_FRAMEBUFFER,0)
      self.drawQuad(tex=RT["texture"])
    
    glutSwapBuffers()
    
  def drawQuad(self,tex):
    glUseProgram(self.programs["quad"])
    
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_BLEND)
    glClearColor(0,0,0,1)
    glClear( GL_COLOR_BUFFER_BIT |
             GL_DEPTH_BUFFER_BIT )
    
    key = ("quad", "tex1")
    glUniform1i( self.attribs[key], tex )
    
    mouseey = (1.0*self.H-self.mousehovery)/self.H
    #mouseey = (mouseey-0.5)*self.H/self.W
    #mouseey = (mouseey)+0.5
    key = ("quad", "mouse")
    glUniform3f( self.attribs[key],
      1.0*self.mousehoverx/self.W, 
      mouseey,
      np.mod(self.tg,2*np.pi))
    
    glBindVertexArray(self.arrays["quad"])
    glDrawArrays(
      GL_TRIANGLE_STRIP,
      0,
      4 )
    glBindVertexArray(0)
    
  def drawSwarm(self):
    glUseProgram(self.programs["swarm"])
    
    RT = 1 - self.renderstatus
    glBindFramebuffer(GL_FRAMEBUFFER,
      self.RenderTargets[RT]["framebuffer"])
    glViewport(0, 0, 
      self.RenderTargets[RT]["width"],
      self.RenderTargets[RT]["height"])
    
    key = ("swarm", "dt")
    glUniform1f( self.attribs[key],
      #self.rendertimeg )
      1.0/120 )
    key = ("swarm","rot")
    glUniform1f( self.attribs[key],
      np.mod(self.tg*np.pi/16,2*np.pi) )    
    
    key = ("swarm","textex")
    glUniform1i( self.attribs[key],
      self.RenderTargets[1-RT]["texture"] )
    key = ("swarm","textex2")
    glUniform1i( self.attribs[key],
      self.RenderTargets[1-RT]["texture2"] )
    
    key = ("swarm", "dims")
    glUniform3f( self.attribs[key],
      self.W, self.H, 1.0*self.W/self.H )
    key = ("swarm","R")
    glUniform1f( self.attribs[key],
      self.R )
    key = ("swarm","C")
    glUniform1f( self.attribs[key],
      self.C )
    
    mouseey = (1.0*self.H-self.mousey)/self.H
    mouseey = (mouseey-0.5)*self.H/self.W
    mouseey = (mouseey)+0.5
    key = ("swarm", "mouse")
    glUniform3f( self.attribs[key],
      1.0*self.mousex/self.W, 
      mouseey,
      -1 if self.mousedown else 1 )
    glBindVertexArray(self.arrays["square"])
    
    glDisable( GL_DEPTH_TEST )
    glDisable( GL_BLEND )
    glPointSize(1)
    glDrawArrays(
      GL_POINTS,
      0,
      self.R*self.C )
    glBindVertexArray(0)    
    self.renderstatus = 1 - self.renderstatus
    
  def drawSquares(self):
    glUseProgram(self.programs["square"])
    
    key = ("square","textex")
    glUniform1i( self.attribs[key],
      #self.textures["me"] )
      self.RenderTargets[self.renderstatus]["texture"] )
    
    key = ("square", "cols")
    glUniformMatrix3fv(
      self.attribs[key],1,False,self.matV)
    
    key = ("square", "alpha")
    
    glUniform1f(self.attribs[key],
      0.9 if self.points else 0.25 )
    
    key = ("square", "dims")
    glUniform3f( self.attribs[key],
      self.W, self.H, 1.0*self.W/self.H )
    key = ("square","R")
    glUniform1f( self.attribs[key],
      self.R )
    key = ("square","C")
    glUniform1f( self.attribs[key],
      self.C )

    glDisable( GL_DEPTH_TEST )
    glEnable( GL_BLEND )
    glBlendFunc( GL_SRC_ALPHA, 
                 GL_ONE_MINUS_SRC_ALPHA )
    glBindVertexArray(self.arrays["square"])
    
    glPointSize(self.psize)
    glLineWidth(self.lsize)
    glDrawArrays(
      GL_POINTS if self.points else GL_LINES,
      0,
      self.R*self.C )
    glBindVertexArray(0)
    
  def drawTri(self, tex):
    glUseProgram(self.programs["tri"])    
    
    key = ("tri","c")
    self.loadData(key,
      np.array(self.tripos,"float32") )
    
    ids = np.array([0,1,2],"float32")
    key = ("tri","id")
    self.loadData(key,ids)
    
    key = ("tri","textex")
    glUniform1i( self.attribs[key],tex )
    
    key = ("tri","rot")
    glUniform1f( self.attribs[key],
      np.mod(self.tg*np.pi/2,2*np.pi) )
    
    glBindVertexArray(self.arrays["tri"])
    glDrawArrays(
      GL_TRIANGLE_STRIP,
      0,
      3 )
    glBindVertexArray(0)

  def drawBackground(self):    
    #glClearColor( 0, 0, 0, 0 )
    c = np.sin( 2*np.pi*self.randfreqs*self.tg/4 )
    c = (c + 1) / 2
    self.tripos = np.array(c)
    
    if self.rendertotexture:
      c *= 0.5
      c += 0.25
    else:
      c = 0*c + 0.1
    self.tricol = np.array(c)
    #self.tripos = self.tripos*0+1
    glClearColor(c[0], c[1], c[2], 1.0)
    
    glEnable( GL_BLEND )
    glEnable( GL_DEPTH_TEST )
    glBlendFunc( GL_SRC_ALPHA, 
                 GL_ONE_MINUS_SRC_ALPHA )
    glClear( GL_COLOR_BUFFER_BIT |
             GL_DEPTH_BUFFER_BIT )

  def ResizeGL( self, *args ):
    self.W, self.H = args
    self.initMouse()
    self.loadRenderTargets()
    
  def initMouse(self):
    self.mousex = self.W*.5
    self.mousey = self.H*.5
    self.mousehoverx = self.mousex
    self.mousehovery = self.mousey
  
  matV = np.eye(3)
  def transitionColors(self):
    try:
      thread.start_new_thread(
        self.transitionColorsThread,())
    except:
      print( "Problems starting a thread? :(" )
    
  def transitionColorsThread(self,delta=0.25):
    self.oldMatV = self.matV
    self.newV = self.permute()
    ts = self.tg
    a = 0
    while a < delta:
      a = self.tg - ts
      self.matV = (a*self.newV + 
                   (1-a)*self.oldMatV)
      time.sleep(0.05)
  
  perms = IT.cycle( IT.permutations([1,2,0]) )
  def permute(self):
    p = next(self.perms)
    x = np.eye(3)
    x[0,p[0]] = 1
    x[1,p[1]] = 1
    x[2,p[2]] = 1
    return x
    
  def writePNG(self, fb = 0, name="screenie"):
    """Write a png file from GL framebuffer.
       Disabled the alpha channel because of
       some weird alpha (maybe due to 
       stacking?)"""
    class SnapThread(threading.Thread):
      def run(self, context, data, name):
        im = Image.frombuffer(
          "RGB", (context.W,context.H), 
          data, "raw", "RGB", 0, 0)
        t = time.strftime( "_%Y_%m_%d_%H%M%S" )
        name = "{}_{:>07.2f}s{}.png".format(
          name, context.t, t)
        print( "Taking Screenshot " + name )
        outdir = os.path.join( 
          os.path.expanduser("~"), 
          "Pictures",
          "opengl_flower")
        if not os.path.exists(outdir):
          os.makedirs(outdir)
        im.save(os.path.join(outdir, name))
    
    tstart = self.get_time()
    glBindFramebuffer(GL_FRAMEBUFFER,fb)
    data = glReadPixels( 0,0, self.W, self.H, 
      GL_RGB, GL_UNSIGNED_BYTE)
    SnapThread().run(self, data, name)
    tend = self.get_time()
    self.tpaused += tend - tstart
    
  def getTex(self, tex, name="texture"):
    """Copy a texture to a file."""
    class SnapThread(threading.Thread):
      def run(self, context, data, w, h, name):
        im = Image.frombuffer(
          "RGBA", (w,h), 
          data, "raw", "RGBA", 0, 0)
        t = time.strftime( "_%Y_%m_%d_%H%M%S" )
        name = "{}_{:>07.2f}s{}.png".format(
          name, context.t, t)
        #print( "Writing texture " + name )
        outdir = os.path.join( 
          os.path.expanduser("~"), 
          "Pictures",
          "opengl_flower")
        if not os.path.exists(outdir):
          os.makedirs(outdir)
        im.save(os.path.join(outdir, name))
    tstart = self.get_time()
    
    glBindTexture(GL_TEXTURE_2D, tex)
    w = glGetTexLevelParameteriv(
      GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH )
    h = glGetTexLevelParameteriv(
      GL_TEXTURE_2D, 0, GL_TEXTURE_HEIGHT )    
    data = glGetTexImage( GL_TEXTURE_2D, 0,
      GL_RGBA, GL_UNSIGNED_BYTE )
    SnapThread().run(self, data, w, h, name)
    tend = self.get_time()
    self.tpaused += tend - tstart
  
if __name__ == "__main__":
  g = Context()
