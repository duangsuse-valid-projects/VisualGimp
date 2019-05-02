# -*- encoding: utf-8 -*-

GIMP_API = 'GimpApi.py'

from os import linesep as sep
from re import match, compile

LET_RE = compile(r'(\w+)\s*=\s*(.+)$')

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

from Tkinter import *

Tk = Tk or globals()['Tk']

# __import__('os').chdir('/home/DuangSUSE/Projects/VisualGimp/')
# GEPL = True; execfile('GimpApi.py'); execfile('VisualGimp.py')

#from __builtin___ import execfile

require = lambda x: globals()[x]

_globalq = require('_globalq')
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

class Gui:
  ''' The GUI interface of this program '''

  def __init__(self, visual):
    self.ds = visual # data source

    self.lastTrace = None
    self.thisTrace = None
    self.lastArrowSet = 0

    self.ui = Tk()
    self.sync = Button(self.ui, text = "Sync variable trace", command = self.syncClicked)
    self.update = Button(self.ui, text = "Update variable trace", command = self.updateClicked)

    self.publish = Button(self.ui, text = "Refresh traced arrows", command = self.refreshFrame)

    self.code_rst = Button(self.ui, text = "Move code arrow 0", command = self.crReset)
    self.code_mup = Button(self.ui, text = "Move code arrow ↑", command = self.crInc)
    self.code_mdn = Button(self.ui, text = "Move code arrow ↓", command = self.crDec)

  def show(self):
    name = Label(self.ui, text = " - Variable Trace Text Layer - ", justify = CENTER, anchor = W, fg = "green")
    name.pack()

    self.sync.pack()
    self.update.pack()

    separator = Frame(self.ui, height = 5, bd = 1, relief = SUNKEN)
    separator.pack(fill=X, padx=5, pady=20)

    self.publish.pack()

    separator1 = Frame(self.ui, height = 10, bd = 1, relief = SUNKEN, bg = "green")
    separator1.pack(fill=X, padx=2, pady=2)

    name1 = Label(self.ui, text = " - Code Pointer Control - ", justify = CENTER, fg = "green")
    name1.pack()

    self.code_rst.pack()
    self.code_mup.pack()
    self.code_mdn.pack()

    self.ui.wm_deiconify()
    self.ui.wm_title(VisualGimp.__name__)
    self.ui.wm_minsize(330, 500)
    self.ui.wm_attributes('-topmost')

    self.focus()

    mainloop()

  def focus(self): self.ui.focus_set()

  def syncClicked(self):
    pass
  def updateClicked(self):
    pass
  def refreshFrame(self):
    pass

  def crReset(self):
    pass
  def crInc(self):
    pass
  def crDec(self):
    pass

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

  def traceMap(self):
    ''' Get value trace map from source '''
    marks = self.text_layer_marks(self.traceLayer)
    lines = GimpAccess.trimMarks(marks).split(sep)
    matches = map(lambda l: globals()['uh'](LET_RE.match(l).groups(), lambda x: x[0:2]), filter(lambda l: l.strip()!='', lines))
    result = dict()
    #print(matches)
    for (k, v) in matches:
      result[k] = v
    return result

  ensure = lambda oid: globals()[oid]

  from Markup import MarkupBuilder as Builder

  _TEMPLATE = Builder()
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
    join = lambda a, l: globals()['stream_join'](a, globals()['nseq']("\n", l - 1))
    joinl = lambda l: join(l, len(l))
    template = self.TEMPLATE0 if updated else "{} = {}"
    # Bad flip_join = curry2(flip(joinl))("\n")
    text = ensure('compose')(ensure('concat_stream'), joinl)(map(lambda i: template.format(i[0], i[1], color = self.rgb2Hex(self.forecolor)), trace.items()))
    return self.TEMPLATE1.format(text, color = '#000000')

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
    return self.l_pts
  codePointerLayer = property(_codePointerLayer)

  def pointerLayerOf(self, name):
    ''' Get the pointers layer of visual '''
    return self.layer_index(self.codePointerLayer, "p%ss" % name.lower())

  def valLayerOf(self, name):
    ''' Get the value layer of visual '''
    return self.layer_index(self.valLayer, 'v' + name)

  def main(self):
    ''' Run this Python helper '''
    self.check_layers()
    Gui(self).show()

if __name__ == '__main__': up()
