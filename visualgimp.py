#!/usr/bin/env python

# -*- coding: utf-8 -*-

from sys import path as pypath
from os import path
from inspect import getfile, currentframe

from gimpfu import *

from gimp import get_progname

#prog = path.basename(__file__) + path.sep + __file__ #gimp.get_progname()
#dir = path.split(prog)[0]

dir = path.dirname(path.abspath(getfile(currentframe())))

pypath.append(dir + path.sep + 'VisualGimp')

from VisualGimp import VisualGimp

# Method #1

# __import__('os').chdir('/home/DuangSUSE/Projects/VisualGimp/')
# from sys import path
# path.append('.')
# execfile('plugin.py')

# Method #2

# Copy visualgimp.py and VisualGimp to:

# GIMP 2.10: ~/.config/GIMP/2.10/plug-ins/
# GIMP 2.8: ~/.gimp-2.8/plug-ins/

def python_visualgimp(asy = False):
  #VisualGimp.up()
  v = VisualGimp(gimp)
  v.check_layers()
  v.main()
  if asy:
    v.gui.app_start()
  else: # main script thread
    v.gui.show()
    v.gui.ui.mainloop()

# Python plugin registration
plug_name = "python_fu_visualgimp"
plug_desc = "Make pointer-based algorithm visualization with GIMP"
plug_desc_short = plug_desc
plug_auth = "duangsuse"
plug_year = '2019'
plug_copy = "Copyright (c) {} duangsuse, Licenced under the MIT License".format(plug_year)
plug_params = []#[(PF_BOOL, "async", "Run in async mode", False)]
plug_results = []

register(
  plug_name,
  plug_desc_short,
  plug_desc,
  plug_auth,
  plug_copy,
  plug_year,
  "Run VisualGIMP",
  "*",
  plug_params,
  plug_results,
  python_visualgimp, menu='<Image>/Filters/Languages/Python-Fu')

#if '.' not in pypath:
main()

