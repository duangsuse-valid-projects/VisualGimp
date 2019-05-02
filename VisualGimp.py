# -*- encoding: utf-8 -*-

GIMP_API = 'GimpApi.py'

from os import linesep as sep
from re import match, compile

from threading import Thread

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
  return v

class Gui:
  ''' The GUI interface of this program '''

  CODE_PTR_MESG = " - Code Pointer Control @ %i - "

  def __init__(self, visual):
    self.ds = visual # data source

    self.lastTrace = None
    self.thisTrace = None

    self.codeArrow = None
    self.lastArrowSet = 0 # code arrow

    self.ui = Tk()
    self.sync = Button(self.ui, text = "Sync variable trace", command = self.syncClicked)
    self.update = Button(self.ui, text = "Update variable trace", command = self.updateClicked)

    self.publish = Button(self.ui, text = "Refresh traced arrows", command = self.refreshFrame)

    self.code_rst = Button(self.ui, text = "Move code arrow 0", command = self.crReset)
    self.code_mup = Button(self.ui, text = "Move code arrow ↑", command = self.crDec)
    self.code_mdn = Button(self.ui, text = "Move code arrow ↓", command = self.crInc)

    self.export_index = 0
    self.export_code = Entry(self.ui)
    self.export = Button(self.ui, text = "✔ Export Frame", command = self.do_export)

  def show(self):
    name = Label(self.ui, text = " - Variable Trace Text Layer - ", justify = CENTER, anchor = W, fg = "green")
    name.pack()

    self.sync.pack()
    self.update.pack()

    separator = Frame(self.ui, height = 5, bd = 1, relief = FLAT)
    separator.pack(fill=X, padx=5, pady=20)

    self.publish.pack()

    separator1 = Frame(self.ui, height = 10, bd = 1, relief = SUNKEN, bg = "green")
    separator1.pack(fill=X, padx=2, pady=2)

    name1 = Label(self.ui, text = self.CODE_PTR_MESG %self.lastArrowSet, justify = CENTER, fg = "green")
    name1.pack()
    self.codeArrow = name1

    self.code_rst.pack()
    self.code_mup.pack()
    self.code_mdn.pack()

    separator2 = Frame(height=20, bd=1, relief=FLAT)
    separator2.pack(fill=X, padx=20, pady=5)

    self.export.pack()
    name2 = Label(self.ui, text = "When exporting, run these code:", justify=CENTER, fg="red")
    name2.pack()
    self.export_code.pack()

    self.ui.wm_deiconify()
    self.ui.wm_title(VisualGimp.__name__)
    self.ui.wm_minsize(330, 500)
    self.ui.wm_attributes('-topmost')

    self.focus()

    fn = self.ui.mainloop
    loop = Thread(target=fn)
    loop.setDaemon(False)
    loop.setName("Tk event loop thread")
    loop.start()
    loop.join()

  def focus(self): self.ui.focus_set()

  def syncClicked(self):
    pass
  def updateClicked(self):
    pass
  def refreshFrame(self):
    pass

  def do_export(self):
    pass

  # 辣鸡代码，请见谅
  def cr_children(self): return self.ds.layer_get_children(self.ds.codePointerLayer)
  def cr_hide_last(self, childs): self.ds.layer_hide(childs[self.lastArrowSet])
  def cr_overflow(self, off): return self.lastArrowSet + off not in range(0, len(self.cr_children())) or len(self.cr_children()) == 0
  def cr_refresh(self):
    it = self.ds.codePointerLayer
    it.update(0, 0, it.width, it.height)
  def crReset(self):
    ''' Reset code cursor '''
    for l in self.cr_children():
      self.ds.layer_hide(l)
    children = self.cr_children()
    if children >= 1:
      self.ds.layer_show(children[0])
    self.lastArrowSet = 0
    self.codeArrow.text = self.CODE_PTR_MESG % 0
    self.codeArrow.update()
    #self.cr_refresh()
  def crInc(self):
    if self.cr_overflow(1): return
    children = self.cr_children()
    self.cr_hide_last(children)
    last = self.lastArrowSet
    self.ds.layer_show(children[last + 1])
    self.lastArrowSet += 1
    self.codeArrow.text = self.CODE_PTR_MESG % (last + 1)
    self.codeArrow.update()
    #self.cr_refresh()
  def crDec(self):
    if self.cr_overflow(-1): return
    children = self.cr_children()
    self.cr_hide_last(children)
    last = self.lastArrowSet
    self.ds.layer_show(children[last - 1])
    self.lastArrowSet -= 1
    self.codeArrow.text = self.CODE_PTR_MESG % (last - 1)
    self.codeArrow.update()
    #self.cr_refresh()

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
    self.gui.show()

if __name__ == '__main__': VG = up()
