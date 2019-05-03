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

#from multiprocessing.pool import Pool

def ap(f, *args, **kwargs):
  ''' Apply a applicative object with given arguments '''
  if len(args) == 0: return f(**kwargs)
  fn = f; argc = len(args)
  argp = 0
  while callable(fn) and argp < argc:
    if fn.func_code.co_argcount == 1:
      fn = fn.__call__(args[argp], **kwargs)
    else:
      fn = fn.__call__(*args, **kwargs)
    argp += 1
  return fn

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

def coerce(x, t): return x.__coerce__(t)
def unreachable(): raise RuntimeError('Corrupted state : Impossible code path reached !!!')

def foldl(op):
  ''' Fold left definition like the one with same name in Haskell '''
  def foldl_init(val):
    def foldl_ls(ls):
      # foldl f v (x:xs) = foldl f (f v x) xs
      #if ls == []: return val
      def foldl_ac(head = 0):
        if head >= len(ls): return val
        x = ls[head]#; xs = [] if head+1 >= len(ls) else ls[head+1:len(ls)]
        return foldl_init(op(val, x))(ls)(head+1)
      return foldl_ac
    return foldl_ls
  return foldl_init

class Maybe:
  ''' Nullable value '''
  def __init__(self, obj):
    ''' Make a (maybe None) value wrapper '''
    self.obj = obj
    self.is_null = obj is None

  def is_none(self):
    ''' Return True if wrapped object is None '''
    return self.is_null
  def is_any(self):
    ''' Return True if wrapped object is not None '''
    return not self.null
  null = property(is_none)
  any = property(is_any)

  def must_get(self):
    ''' Get value or raise AssertionError (if none) '''
    if self.null:
      raise AssertionError('Object is None')
    else: return self.obj

  def get(self):
    ''' Get value or return Nothing Maybe '''
    if self.null: return Nothing
    else: return self.obj

  def get_or(self, fn_x_obj):
    ''' Get value or else... (callable or alternative value) '''
    if self.null:
      if callable(fn_x_obj): return fn_x_obj()
      else: return fn_x_obj
    else: return self.obj

  def flat_map(self, fn):
    ''' If obj is null, return obj, else fn(obj) '''
    result = fn(self.obj) if not self.null else None
    return result

  def map(self, fn):
    ''' If obj is null, return Nothing, else compose(Maybe, fn)(obj) '''
    return Maybe(self.flat_map(fn))

  def __str__(self):
    tt = type(self.obj) if self.any else object
    typenam = '%s?' % tt.__name__
    return '{}({})'.format(typenam, self.obj)

  def __or__(self, other):
    ''' this any or other any '''
    if self.any: return self
    else: return other

  def __coerce__(self, newtype):
    if self.any:
      return self.get().__coerce__(newtype)
    else:
      raise TypeError('Cannot convert Nothing nullable to type %s' %newtype.__name__)

Nothing = Maybe(None) # 没有所谓的类型，值才有类型...
Just = Maybe

def maybe(default, fn, may):
  '''
  takes a default value, a function, and a Maybe value. If the Maybe value is Nothing, the function returns the default value.
  Otherwise, it applies the function to the value inside the Just and returns the result.
  See: Maybe.flat_map
  Equivalent: flat_map with default value
  '''
  if may is Nothing: return default
  else: fn(may.get())

def fst(tup): return tup[0]
def snd(tup): return tup[1]

def lastindex(xs): return len(xs) -1
def head(xs, off=0): return xs[off]
def tail(xs, off=0): return xs[off+1:lastindex(xs)]

def first_just(ls):
  ''' Find first Just in a maybe list '''
  if type(ls) is list:
    return foldl(Maybe.__or__)(Nothing)(ls)()
  else:
    res = filter(Maybe.is_any, ls)
    if len(res) is 0: return Nothing
    else: return iter(res).next()

class Either:
  ''' Either value a or b '''
  def __init__(self, a_v, b_v):
    self.a = a_v; self.b = b_v

  def is_left(self):
    pass
  def is_right(self):
    pass

  left = property(is_left)
  right = property(is_right)

  def get_left_or(self, fn_x_v):
    pass
  def get_right_or(self, fn_x_v):
    pass

  def get_left(self):
    pass
  def get_right(self):
    pass

  l = property(get_left)
  r = property(get_right)

  def must_get_left(self):
    pass
  def must_get_right(self):
    pass

  def either(self, fl, fr):
    pass

  def swap(self):
    pass

  def map_l(self, fl):
    pass

  def map_r(self, fr):
    pass

  def flat_map_l(self, fn):
    pass

  def flat_map_r(self, fn):
    pass

  def map(self, fl): return self.map_l(fl)
  def flat_map(self, fl): return self.flat_map_l(fl)


def Left(a): return Either(a, None)
def Right(b): return Either(None, b)

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

