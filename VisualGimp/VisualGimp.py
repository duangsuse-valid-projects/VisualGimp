# -*- encoding: utf-8 -*-

GIMP_API = 'GimpApi.py'

from os import linesep as sep
from re import match, compile

from threading import Thread
from time import time

from HBoxie import DictFrame

from collections import deque

from Util import stream_join, concat_stream, nseq, compose, uh, infseq, identitystar, _globalq

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

from tkinter import *

Tk = Tk or globals()['Tk']

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

class Gui (Thread):
  ''' The GUI interface of this program '''

  CODE_PTR_MESG = " - Code Pointer Control @ %i - "

  def __init__(self, visual):
    self.ds = visual # data source
    Thread.__init__(self) # target=run
    self.ui = None

    self.lastTrace = None
    self.thisTrace = {}

    self.codeArrow = None
    self.lastArrowSet = 0 # code arrow

    self.sync = None
    self.update = None

    self.publish = None

    self.code_rst = None
    self.code_mup = None
    self.code_mdn = None
    self.cp_tvar = None

    self.export_index = 0
    self.export_code = None
    self.export = None

    self.export_lambda = identitystar #:0
    self.trace_edits = deque()

    self.trace_ptr_lastshown = {}

  def _export(self):
    ''' increase export index for calling extension lambda '''
    if self.export_lambda is not None: self.export_lambda(self, self.export_index)
    self.export_index += 1
  def __convert_traceDict(self, trace):
    ''' convert and return int trace dict of indices '''
    return dict(map(lambda kv: (kv[0], int(kv[1])), trace.items()))
  _convert_traceDict = __convert_traceDict

  def bind(self):
    ''' Make widgets in app thread '''
    self.ui = Tk()
    self.sync = Button(self.ui, text = "[F1] Sync variable trace", command = self.syncClicked)
    self.dict_view = DictFrame(self.ui)
    self.update = Button(self.ui, text = "[F2] Commit variable trace changes", command = self.updateClicked)
    self.publish = Button(self.ui, text = "→ Refresh traced arrows", command = self.refreshFrame)
    self.code_rst = Button(self.ui, text = "← Move code arrow", command = self.crReset)
    self.code_mup = Button(self.ui, text = "↑ Move code arrow", command = self.crDec)
    self.code_mdn = Button(self.ui, text = "↓ Move code arrow", command = self.crInc)
    self.cp_tvar = StringVar()
    self.cp_tvar.set(self.CODE_PTR_MESG %self.lastArrowSet)
    self.export_code = Entry(self.ui)
    self.convert_trace_code = Entry(self.ui)
    self.btn_update_codes = Button(self.ui, text = "Compile", command = self.updateConverter, justify=CENTER)
    self.export = Button(self.ui, text = "✔ Export Frame", command = self.do_export)
    self.message = StringVar()
    self.message_view = Label(self.ui, textvariable=self.message, justify=CENTER, fg="green")

  def run(self):
    Thread.run(self)
    self.show()
    self.ui.mainloop()

  def app_start(self):
    self.setName('GimpVisual Tk Application at ' + str(time()))
    #self.setDaemon(False)
    self.start()

  def show(self):
    ''' Bind widgets in application thread '''
    self.bind()
    name = Label(self.ui, text = " - Variable Trace Text Layer - ", justify = CENTER, anchor = W, fg = "green")
    name.pack()

    self.sync.pack()
    self.update.pack()

    self.dict_view.pack()

    separator = Frame(self.ui, height = 5, bd = 1, relief = FLAT)
    separator.pack(fill=X, padx=5, pady=20)

    self.publish.pack()

    separator1 = Frame(self.ui, height = 10, bd = 1, relief = SUNKEN, bg = "green")
    separator1.pack(fill=X, padx=2, pady=2)

    name1 = Label(self.ui, textvariable = self.cp_tvar, justify = CENTER, fg = "green")
    name1.pack()
    self.codeArrow = name1

    self.code_rst.pack()
    self.code_mup.pack()
    self.code_mdn.pack()

    separator2 = Frame(self.ui, height=20, bd=1, relief=FLAT)
    separator2.pack(fill=X, padx=20, pady=5)

    self.export.pack()
    name2 = Label(self.ui, text = "When exporting, run these code:", justify=CENTER, fg="red")
    name2.pack()
    self.export_code.pack()

    name3 = Label(self.ui, text = "When converting trace table to indices, run these code:", justify=CENTER, fg="red")
    name3.pack()
    self.convert_trace_code.pack()
    self.btn_update_codes.pack()

    self.message_view.pack()

    self.ui.wm_deiconify()
    self.ui.wm_title(VisualGimp.__name__)
    self.ui.wm_minsize(330, 500)
    self.ui.wm_attributes('-topmost')

    self.focus()
    self.bind_keys()

  def bind_keys(self):
    ''' register key event binding for the root Tk instance '''
    def do_ign2(fn): return lambda _: fn()
    def bind_ign(sig, fn):
      self.ui.bind(sig, do_ign2(fn))

    bind_ign('<Left>', self.crReset)
    bind_ign('<Right>', self.refreshFrame)
    bind_ign('<Up>', self.crDec)
    bind_ign('<Down>', self.crInc)

    bind_ign('<Return>', self.do_export)

    bind_ign('<F1>', self.syncClicked)
    bind_ign('<F2>', self.updateClicked)

  def focus(self): self.ui.focus_set()

  def syncClicked(self):
    ''' update dictview '''
    traces = self.ds.traceMap()
    if traces is None:
      self.message.set('Cannot read trace pattern!')
      return
    self.lastTrace = traces if self.lastTrace is None else self.thisTrace
    self.thisTrace = traces
    self.dict_view.destroy()
    self.dict_view = DictFrame(self.ui, traces)
    self.dict_view.listen(self.updateTrace())
    self.dict_view.pack()

  def updateTrace(self):
    def listener(index, key, oldvalue, newvalue):
      newdict = self.thisTrace.copy()
      evaluated = ':('
      try:
        evaluated = compose(str, eval)(newvalue)
      except Exception as e:
        evaluated = str(e)
      newdict[key] = evaluated
      self.message.set('records[{}] = {} evaluated to {}'.format(key, newvalue, evaluated))
      field = self.dict_view.ivs[index].b
      field.delete(0, END)
      field.insert(0, evaluated)
      changed = False
      for key in newdict:
        if key not in self.lastTrace or newdict[key] != self.lastTrace[key]:
          changed = True
          break
      if changed:
        self.trace_edits.append((key, evaluated))
        self.thisTrace[key] = evaluated # apply changes to current map
      #print(key, newvalue)
    return listener

  def updateClicked(self):
    changeset_count = 0
    while len(self.trace_edits) !=0:
      (k, nv) = self.trace_edits.popleft()
      #print((k, nv))
      self.lastTrace[k] = nv # Update GIMP textual trace repr
      changeset_count += 1
    #print(self.lastTrace)
    if changeset_count != 0: self.ds.text_layer_marks_set(self.ds.traceLayer, self.ds.formatTrace(self.lastTrace, True))
    self.message.set('{} records updated'.format(changeset_count))

  FRAME_PATTERN = compile(r'^(\w+) by (\w+)$')
  def refreshFrame(self):
    refreshing = [] # name to trace record (str by lastPath)
    for k in self.ds.visualLayer.children:
      spec = k.name
      m = self.FRAME_PATTERN.match(spec)
      groups = uh(m, lambda m: m.groups())
      if groups is not None and len(groups) == 2:
        refreshing.append((groups[1], groups[0]))
      else:
        self.ds.message('Failed matching name {}, try follow pattern of `pointerName by traceVariable`?'.format(spec))

    t2n = dict(refreshing)
    #print(t2n)
    origin = self.thisTrace
    mapped = self._convert_traceDict(self.thisTrace)
    #print(mapped)
    msg = str()
    for key in origin.keys():
      #print(k)
      if key not in t2n or key not in mapped: continue
      ptr = mapped[key]
      layer = self.ds.pointerLayerOf(t2n[key])
      #print(ptr, layer)
      if key in self.trace_ptr_lastshown:
        self.ds.layer_hide(layer.children[self.trace_ptr_lastshown[key]])

      if not self.ds.layer_is_group(layer) or len(layer.children) <= ptr:
        self.ds.message('Failed to change cursor for {}: Not a group or length </= index {} '.format(key, ptr))
      self.ds.layer_show(layer.children[ptr])
      msg += 'Showing cursor {} @ position {}'.format(layer.name, ptr) + '\n'
      self.trace_ptr_lastshown[key] = ptr
    self.message.set(msg)

  def do_export(self):
    self._export()

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
    self.cp_tvar.set( self.CODE_PTR_MESG % 0 )
    self.codeArrow.update()
    #self.cr_refresh()
  def crInc(self):
    if self.cr_overflow(1): return
    children = self.cr_children()
    self.cr_hide_last(children)
    last = self.lastArrowSet
    self.ds.layer_show(children[last + 1])
    self.lastArrowSet += 1
    self.cp_tvar.set( self.CODE_PTR_MESG % (last + 1) )
    self.codeArrow.update()
    #self.cr_refresh()
  def crDec(self):
    if self.cr_overflow(-1): return
    children = self.cr_children()
    self.cr_hide_last(children)
    last = self.lastArrowSet
    self.ds.layer_show(children[last - 1])
    self.lastArrowSet -= 1
    self.cp_tvar.set( self.CODE_PTR_MESG % (last - 1) )
    #self.codeArrow.update()
    #self.cr_refresh()

  def updateConverter(self):
    code_trace = self.convert_trace_code.get()
    code_export = self.export_code.get()
    info = list()

    def compile_item(name, code, info):
      result = identitystar #;;
      try:
        result = eval(code)
      except Exception as e:
        info.append( '**{}'.format(str(e)) )
      info.append( 'Compiled {} lambda: {}\n'.format(name, str(result)) )
      return result

    if len(code_export) is not 0: self.export_lambda = compile_item('export', code_export, info)
    if len(code_trace) is not 0: self._convert_traceDict = compile_item('trace', code_trace, info)
    self.message.set(concat_stream(stream_join(info, infseq("\n"))))

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
