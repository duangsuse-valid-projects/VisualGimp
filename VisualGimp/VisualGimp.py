#!/usr/bin/env python2
# -*- encoding: utf-8 -*-

GIMP_API = 'GimpApi.py'

from os import linesep as sep
from re import match, compile as re_compile

from Util import stream_join, concat_stream, nseq, compose, uh, infseq, identitystar, _globalq

from Gui import Gui

LET_RE = re_compile(r'(\w+)\s*=\s*(.+)$')

# Gimp Python Script-Fu REPL, without import path configured correctly
def isGEPL():
  try: return globals()['GEPL'] == True
  except KeyError: return False

if not isGEPL():
  GimpAccess = __import__('GimpApi', ['GimpAccess']).GimpAccess
elif (lambda x: x.access(GIMP_API, x.R_OK))(__import__('os')):
    with open(GIMP_API) as f:
      exec(f.read())
else:
  raise LookupError('Failed to execute API delegate!')

#Tk = Tk or globals()['Tk']

# __import__('os').chdir('/home/DuangSUSE/Projects/VisualGimp/')
# GEPL = True; execfile('GimpApi.py'); execfile('VisualGimp.py')

#from __builtin__ import execfile

require = lambda x: globals()[x]

execfile = _globalq('execfile')

from io import FileIO

if (callable(execfile) is not True):
  def __execfile(name):
    try:
      f = FileIO(name)
      codestr = f.read()
      exec(codestr)
    except:
      raise RuntimeError('Failed to execute file %s' % name)
    finally: f.close()
  if execfile is None: execfile = __execfile
  #del __execfile

def up():
  #execfile('VisualGimp.py')
  v = VisualGimp(globals()['gimp'])
  v.check_layers()
  v.main()
  return v

class VisualGimp (GimpAccess):
  '''
  VisualGimp GIMP program data algorithm visualation helper
  with GIMP Python API and TkInter

  author: duangsuse
  date: Apr, 2019
  '''

  def _initialized(self):
    instance = self()
    instance.check_layers()
    return instance

  init = classmethod(_initialized)

  def check_layers(self):
    ''' Register and check for VisualGimp layers '''

    def checkLayer(name):
      try:
        return self.single_layer_root(name)
      except IndexError as e:
        self.message(e)
        return None

    def layerGroup(layerCheckFn):
      ''' Ensures a layer is a layer group, or display script error message '''
      def _check(x):
        result = layerCheckFn(x)
        if result is None or not self.layer_is_group(result):
          name = result.name if result else '*missing %s*' % x
          message = '-*- VisualGimp Data ERROR -*- %s is NOT a group layer' % name
          self.message(message)
          raise TypeError(message)
        return result
      return _check

    checkLayerGroup = layerGroup(checkLayer)

    self.l_code = checkLayer('Code')
    self.l_vals = checkLayerGroup('Vals')

    self.l_trace = checkLayer('Trace')
    self.l_vis = checkLayerGroup('Visual')
    self.l_pts = checkLayerGroup('Pointers')
    self.l_cpt = self.pointerLayerOf('code')

  def traceMap(self):
    ''' Get value trace map from source '''
    marks = self.text_layer_marks(self.traceLayer)
    lines = GimpAccess.trimMarks(marks).split(sep)
    vallines = filter(lambda l: l.strip()!='', lines)
    matches = map(lambda l: uh(LET_RE.match(l), lambda x: x.groups()[0:2]), vallines)
    result = dict()
    #print(matches)
    #if type(matches) is not type(None):?????
    it = matches.__iter__().next() if len(matches) > 0 else None
    if it is not None:
      #print(matches)
      for kv in matches:
        #print(k,v)
        if kv is not None:
          (k, v) = kv
          result[k] = v
        else: return None
      return result
    else: return None

  ensure = lambda oid: globals()[oid]

  from Markup import MarkupBuilder as Builder

  _TEMPLATE = Builder()
  _TEMPLATE < '{} = '
  _TEMPLATE.begin('span', {'foreground': '{color}'})
  _TEMPLATE < '{}'
  _TEMPLATE <= 1

  #with _TEMPLATE.tag("span", foreground = '#66ccff'):
  #  _TEMPLATE < 'QwQ' < 'Ror'
  #  _TEMPLATE > 'i'
  #  _TEMPLATE < 'italic'
  #  _TEMPLATE <= 1
  #  _TEMPLATE >= ['a', {'id': 'message'}]
  #  _TEMPLATE.text("Hello~")
  #  _TEMPLATE <= 1

  # <span foreground="{}">{}</span><span foreground="#66ccff">QwQ<i>italic</i><a id="message">Hello~</a></span>

  TEMPLATE0 = _TEMPLATE.make()

  del _TEMPLATE

  _TEMPLATE = Builder()
  _TEMPLATE > 'markup'
  _TEMPLATE < '{}'
  _TEMPLATE <= 1
  TEMPLATE1 = _TEMPLATE.make()
  del _TEMPLATE

  def formatTrace(self, trace, updated = False):
    def ensure(name): return globals()[name]
    ''' Make a new colored (foreground) markup for value trace '''
    #curry2 = ensure('curry2L')
    #flip = ensure('flipL')
    join = lambda a, l: stream_join(a, nseq("\n", l - 1))
    joinl = lambda l: join(l, len(l))
    template = self.TEMPLATE0 if updated else "{} = {}"
    # Bad flip_join = curry2(flip(joinl))("\n")
    text = compose(concat_stream, joinl)(map(lambda i: template.format(i[0], i[1], color = self.rgb2Hex(self.forecolor)), trace.items()))
    #print(self.TEMPLATE1.format(text))
    return self.TEMPLATE1.format(text)

  def setTrace(self, *args, **kwargs):
    ''' Sets trace by map '''
    self.text_layer_marks_set(self.traceLayer, self.formatTrace(*args, **kwargs))

  def _codeLayer(self): return self.l_code
  codeLayer = property(_codeLayer)
  def _traceLayer(self): return self.l_trace
  traceLayer = property(_traceLayer)
  def _visualLayers(self): return self.l_vis
  visualLayer = property(_visualLayers)
  def _valLayers(self): return self.l_vals
  valLayer = property(_valLayers)

  def _codePointerLayer(self):
    ''' Get code pointers layer '''
    return self.l_cpt
  codePointerLayer = property(_codePointerLayer)

  def pointerLayerOf(self, name):
    ''' Get the pointers layer of visual '''
    return self.layer_index(self.l_pts, "p%ss" % name.lower())

  def valLayerOf(self, name):
    ''' Get the value layer of visual '''
    return self.layer_index(self.valLayer, 'v' + name)

  def main(self):
    ''' Run this Python helper '''
    self.check_layers()
    self.gui = Gui(self)
    #self.gui.app_start()

if __name__ == '__main__': VG = up()

