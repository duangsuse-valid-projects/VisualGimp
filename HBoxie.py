# coding: utf-8

from tkinter import Frame, LEFT, RIGHT, Label, Entry, Button, END

class TripleFrame:
  '''
  A frame renders a triple (or pair) of widget

  pair = TripleFrame(root, Label, lambda pf: Button(pf, text = "Hello"))
  '''
  def __init__(self, parent, a, b, c=None, pad=20):
    self.parent = parent
    self.frame = Frame()
    self.wa = a(self.frame); self.wb = b(self.frame)
    if c is not None: self.wc = c(self.frame)
    self.pad = pad
  def pack(self):
    ''' register to parent container '''
    self.frame.pack()
    self.wa.pack(side=LEFT, padx=self.pad)
    if self.wc is not None: self.wc.pack(side=RIGHT)
    self.wb.pack(side=RIGHT, padx=self.pad)
  def destroy(self):
    self.wa.forget(); self.wa.destroy()
    self.wb.forget(); self.wb.destroy()
    if self.wc is not None: self.wc.forget(); self.wc.destroy()
    self.frame.destroy()
  def get_a(self): return self.wa
  def get_b(self): return self.wb
  def get_c(self): return self.wc
  a = property(get_a)
  b = property(get_b)
  c = property(get_c)

class DictFrame:
  '''
  A frame renders a Python dict data strucure

  dict_view = DictFrame(root)
  dict_view.update({'a' : '1'})
  dict_view.keychanged = self.onKeyChanged
  '''
  def __init__(self, parent, dict={}):
    self.parent = parent
    self.listener = None
    self.dict = dict
    self.ivs = []; self.keys = []
    def check_failure(t, item):
      raise AssertionError('{} of dict must be string ({} is {})'.format(t, str(item), type(item)))
    for (k, v) in dict.items():
      if type(k) is not str: check_failure('Key', k)
      if type(v) is not str: check_failure('Value', v)

  def pack(self):
    ''' Draw dict frame list UI '''
    if len(self.dict) is 0: return
    index = 0
    b = lambda p: Button(p, text='✔', command=self.call_changed(index))
    for (k, v) in self.dict.items():
      iv = TripleFrame(self.parent, lambda f: Label(f, text=k), lambda f: Entry(f, text='set %s' %k), b)
      iv.b.delete(0, END)
      iv.b.insert(0, v)
      iv.pack()
      self.keys.append(k)
      self.ivs.append(iv)
      index += 1

  def destroy(self):
    for iv in self.ivs: iv.destroy()

  def listen(self, listener):
    '''
    listen item updated: callback(index, key, oldvalue, newvalue)
    '''
    if not callable(listener): raise AssertionError(str(listener) + ' is NOT callable')
    self.listener = listener

  def call_changed(self, index):
    ''' internal callback dispatcher function '''
    def do_callback():
      item_k = self.keys[index]
      old_value = self.dict[item_k]
      new_value = self.ivs[index].b.get()
      self.listener(index, item_k, old_value, new_value)
      self.dict[item_k] = new_value
    return do_callback
