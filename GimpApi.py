# -*- encoding: utf-8 -*-

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
  ''' Get a global by name or None '''
  _globals = globals()
  if name in _globals: return _globals[name]
  else: return None

def uh(obj, do = lambda x: x):
  ''' if obj is not None, run uh, else return None '''
  if obj is not None: return do(obj)
  else: return None

class GimpAccess:
  '''
  Gimp Api accessing utility
  for Layer and message Api

  author: duangsuse
  '''

  ''' Default name for Gimp API module '''
  GIMP_GLOBAL = 'gimp'

  def __init__(self, gimp = _globalq(GIMP_GLOBAL), pdb = uh(_globalq(GIMP_GLOBAL), lambda o: o.pdb)):
    '''
    Make a new instance with gimp api module and PDB symbol module

    gimp: gimp API module, default from global()
    pdb: PDB CNI binding default gimp.pdb
    '''
    if not callable (gimp.message): raise AssertionError("Not a GIMP")
    if not callable (pdb.gimp_text_layer_get_markup): raise AssertionError("Not GIMP PDB: gimp_text_layer_get_markup checked")

    self.api = gimp
    self.cni = pdb

  def message(self, text):
    ''' Show a gimp status bar message '''
    self.api.message(str(text))

  def get_images(self):
    ''' Return a list of currently opened images '''
    return self.api.image_list()

  ''' Alias for get_images '''
  images = property(get_images)

  def single_image(self, no = -1, fail = 'Expecting {} opened image, found {}', fail_callback = lambda s, m: s.message(m)):
    '''
    Gets a single image from gimp image list

    if no image is opened, call message(fail), throw a LookupError
    if multiply images opened and no = -1, call message(fail)
    or return image list

    no: some int >= 0, index of the image to get from
    fail: if no is not specified, select an error message to be used
    fail_callback: callback with error message, default "message"
    '''
    images = self.get_images()
    images_len = len(images)

    def _fail():
      fail_callback(self, message)
      raise LookupError(message)

    nOz = 0 if no == -1 else no
    message = fail.format(nOz + 1, images_len)
    if images_len == 0: _fail()

    if no != -1:
      if no < images_len:
        return images[no]
      else: _fail()

    if images_len == 1:
      return images[0]
    else: _fail()

  def image_layers(self, image):
    ''' Gets layers from image '''
    if type(image) != self.api.Image: return None
    return image.layers

  def single_layer_root(self, index = None, *args, **kwargs):
    '''
    Gets the layer root from single image list,
    if index is given, subscript result with index,
    supports str (search by name)
    '''

    query = self.image_layers(self.single_image(*args, **kwargs))
    return self.layer_index(query, index)

  def layer_index(self, layers, index):
    '''
      Index a layer with int or string (name)

      raises IndexError if more or less than 1 element found
    '''
    if self.layer_is_group(layers): layers = self.layer_get_children(layers)
    if index is not None:
      if type(index) is str:
        layer_names = map(lambda l: l.name, layers)
        if index not in layer_names: raise IndexError("Cannot find name {} in {} items".format(index, len(layer_names)))
        found = filter(lambda nq: nq[0] == index, zip(layer_names, layers))
        if len(found) != 1: raise IndexError("More or less than 1 element with name %s found in %s" % index % str(layers))
        return list(found)[0][1]
      else: return layers.__getitem__(index)
    else: return layers

  def layer_is_group(self, layer):
    ''' Is this layer a layer group? '''
    return type(layer) == self.api.GroupLayer

  def layer_get_children(self, layer):
    ''' Gets children of the layer '''
    if not self.layer_is_group(layer): return None
    return layer.children

  def layer_hide(self, layer):
    ''' Make the layer hidden '''
    layer.visible = False

  def layer_show(self, layer):
    ''' Make the layer shown '''
    layer.visible = True

  def text_layer_marks(self, layer):
    ''' Get SGML markup of target text layer '''
    marks = self.cni.gimp_text_layer_get_markup(layer)
    if marks is None: return self.cni.gimp_text_layer_get_text(layer)
    return marks

  def text_layer_marks_set(self, layer, marks):
    '''
    Set SGML markup of target text layer

    Notes, marks are striped since Gimp 2.0 does not support reading Pango markups
    '''
    self.cni.gimp_text_layer_set_text(layer, self.trimMarks(marks))

  def layerPath(self, root, path = []):
    ''' index layer base recursively by path array '''

    base = root # base dir
    try:
      hierarchy = path.copy()
    except AttributeError: hierarchy = path
    hierarchy.reverse()
    while base is not None and (base.__class__ == list or self.layer_is_group(base)) and len(hierarchy) != 0:
      base = self.layer_index(base, hierarchy.pop())

    return base

  def _trimMarks(self, m, bracel = '<', bracer = '>'):
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

  trimMarks = classmethod(_trimMarks)

  # Others

  def _hexdigit(self, n): return hex(n)[2:]

  hexDigit = classmethod(_hexdigit)

  def _rgb2Hex(self, rgb):
    # return "#" + hexdigit(rgb.r) + hexdigit(rgb.g) + hexdigit(rgb.b) + hexdigit(rgb.a)
    # Not performant
    def rgb2Int(rgb):
      color32 = int()
      color32 |= rgb[0] << (8 * 3)
      color32 |= rgb[1] << (8 * 2)
      color32 |= rgb[2] << 8
      color32 |= rgb[3]
      return color32
    return "#" + self.hexDigit(rgb2Int(rgb))

  rgb2Hex = classmethod(_rgb2Hex)

  def color_foreground(self):
    ''' Get GIMP instance foreground color '''
    return self.api.get_foreground()

  def color_foreground_set(self, nval):
    ''' Get GIMP instance foreground color '''
    return self.api.set_foreground(nval)

  def color_background(self):
    ''' Get GIMP instance backround color '''
    return self.api.get_background()

  def color_background_set(self, nval):
    ''' Get GIMP instance backround color '''
    return self.api.set_background(nval)

  forecolor = property(color_foreground, color_foreground_set, doc = 'GIMP instance foreground color')
  backcolor = property(color_background, color_background_set, doc = 'GIMP instance foreground color')

class MarkupBuilder:
  ''' Gimp Markup SGML builder '''
  def __init__(self):
    self.marks = str()
    self.tag_stack = list()

  def begin(self, tag, attrs = {}):
    '''
    Make a tag with name and attributes

    Attribute name, value and tag name is escaped
    '''
    attrst = str()
    tagscape = self.escape(tag)

    ary = list(stream_join(attrs.keys(), attrs.values())) if attrs.__class__ is dict else list(attrs)
    if len(attrs) != 0:
      for n in range(0, len(ary), 2):
        attrst += self.escape(str(ary[n]))
        attrst += '='
        #print(ary)
        #print(n)
        attrst += "\"%s\"" % self.escape(str(ary[n+1]))
    self.marks += '<' + tagscape
    if len(attrs) != 0: self.marks += ' '
    self.marks += attrst + '>'
    self.tag_stack.append(tagscape)

  def make(self): return self.marks

  def tag(self, *args, **kwargs):
    r'''
    EDSL using __close__ with syntax

    create nodes like:
    with xml.tag('span', {color: '#66ccff'}):
      xml % 'Q \w\ Q'
    '''
    class TagBuilder:
      def __init__(self, xml):
        self.xml = xml
      def __enter__(self):
        self.xml.begin(*args, attrs = kwargs)
      def __exit__(self, *lveinfo):
        self.xml.end()
    return TagBuilder(self)

  def text(self, content):
    ''' append text content '''
    self.marks += self.escape(content)

  def end(self):
    ''' delimites last tag '''
    self.marks += '</' + self.tag_stack.pop() + '>'

  def _escape(self, xml):
    '''
    Escape XML string

    ' is replaced with &apos;
    " is replaced with &quot;
    & is replaced with &amp;
    < is replaced with &lt;
    > is replaced with &gt;
    '''
    escapes = frozenset("'\"&<>")
    replacement = { '\'': 'apos', '"': 'quot', '&': 'amp', '<': 'lt', '>': 'gt' }

    if len(xml) < 1: return
    output = str()
    for i in range(0, len(xml)):
      char = xml[i]
      if (char in escapes):
        output += '&'
        output += replacement[char]
        output += ';'
      else: output += char
    return output

  escape = classmethod(_escape)

  def __str__(self):
    ''' M(marks)..[tag stack] '''
    return 'M(' + self.marks + ')..' + str(self.tag_stack)

  __lt__ = text
  __gt__ = begin

  def __ge__(self, tag_attr):
    ''' xml >= ['markup', {'name': 'abcs'}] '''
    mark = tag_attr[0]
    attr = tag_attr[1]
    self.begin(mark, attr)

  def __le__(self, n = 1):
    ''' Leave (close) N tags '''
    while n > 0:
      self.end()
      n -= 1

