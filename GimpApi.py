# -*- encoding: utf-8 -*-

# author: duangsuse
# date: May 2019

# Utility toolbox for the GNU image manipulation program

from Util import _globalq, uh, _trimMarks, _hexdigit

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
    layers_name = '*indexable*'
    if self.layer_is_group(layers):
      layers = self.layer_get_children(layers)
      layers_name = layers.name
    if index is not None:
      if type(index) is str:
        layer_names = map(lambda l: l.name, layers)
        if index not in layer_names: raise IndexError("Cannot find name {} in {} items (namely {})".format(index, len(layer_names), layers_name))
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

  trimMarks = staticmethod(_trimMarks)

  # Others

  hexDigit = staticmethod(_hexdigit)

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

