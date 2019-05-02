# -*- encoding: utf-8 -*-

# Simple coding helper

# author: duangsuse
# date: Thu May 02 2019 CST

def infseq(x):
  ''' Infinity generator of x '''
  while True: yield x

def nseq(x, n):
  ''' N length generator of x '''
  while n > 0:
    yield x
    n -= 1

def flip(fn): return lambda x: lambda y: fn(y, x)
def flipL(fn): return lambda x: lambda y: fn(y)(x)

def curry2(fn):
  ''' curry for binary functions '''
  return lambda x: lambda y: fn(x, y)

def curry2L(fn):
  ''' curry for binary lambdas '''
  return lambda x: lambda y: fn(x)(y)

def compose(f, g): return lambda x: f(g(x))

def concat_stream(gen):
  strn = str()
  try:
    while True: strn += gen.next()
  except StopIteration:
    pass
  return strn

def stream_join(xs, ys):
  '''
  Given xs, ys, yields { xs.next, ys.next }...
  '''
  xss = iter(xs)
  yss = iter(ys)
  while True:
    yield xss.next() # StopIteration?
    yield yss.next() # StopIteration?

def _globalq(name):
  ''' Get a (maybe MODULE-wise) global by name or None '''
  _globals = globals()
  if name in _globals: return _globals[name]
  else: return None

def uh(obj, do = lambda x: x):
  ''' if obj is not None, run uh, else return None '''
  if obj is not None: return do(obj)
  else: return None


def _trimMarks(m, bracel = '<', bracer = '>'):
  ''' remove format strs of SGML markup '''
  output = str()
  waitClose = False
  if len(m) == 0: return output
  for i in range(0, len(m)):
    char = m[i]
    if char == bracel: waitClose = True
    if waitClose:
      if char == bracer: waitClose = False
    else: output += char
  return output

def _hexdigit(n): return hex(n)[2:]

