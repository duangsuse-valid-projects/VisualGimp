#!/usr/bin/env python2
# -*- encoding: utf-8 -*-

# Gimp Markup Builder
# author: duangsuse
# date: Thu May 02 2019 CST

from os import linesep

from Util import stream_join

class MarkupBuilder:
  ''' Gimp Markup SGML builder '''
  def __init__(self, indent = -1, nl = linesep, buffer = str):
    self.marks = buffer()
    self.tag_stack = list()

    self.nl = nl
    self.indent = indent
    self.last_spaces = 0

    self.revert_last_indent_size = 0

    self.last_is_text = False

  '''
  Indent rules:

  when starting new tag, write last spaces, last spaces += indent
  if new tag is not text tag start (inner is just text), write newline
  when leaving tag, last spaces -= indent
  '''
  def useindent(self): return self.indent != -1
  indented = property(useindent)
  def wnewline(self):
    ''' see use_indent'''
    self.marks += self.nl
  def windent(self):
    ''' see use_indent'''
    wrote = 0
    for _ in range(0, self.last_spaces):
      self.marks += ' '
      wrote += 1 # dummy?
    return wrote
  def cancel_indent(self):
    ''' cancel last indent '''
    if self.indented: self.marks = self.marks[:-self.revert_last_indent_size]
  def do_indent(self, entering = True):
    ''' Write indent, increase last_spaces, saving wrote spaces and newline to revert_last_indent_size '''
    def do():
      self.wnewline()
      if (entering):
        self.last_spaces += self.indent
      else: self.last_spaces -= self.indent
      self.revert_last_indent_size = self.windent() +1
    if self.indented: do()

  def do_last_indent(self, *args, **kwargs):
    ''' write indenting for last block '''
    self.last_spaces -= self.indent
    self.do_indent(*args, **kwargs)
    self.last_spaces += self.indent

  def begin(self, tag, attrs = {}):
    '''
    Make a tag with name and attributes

    Attribute name, value and tag name is escaped
    '''
    self.last_is_text = False
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

    # always write indents for next line
    # makes its possible to drop last indent (text tag)
    self.do_indent()

    self.tag_stack.append(tagscape)
    return self

  def make(self): return self.marks

  def tag(self, *args, **kwargs):
    r'''
    EDSL using __close__ with syntax

    create nodes like:
    with xml.tag('span', {color: '#66ccff'}):
      xml % 'Q \w\ Q'
    '''
    self.last_is_text = False
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
    self.last_is_text = True
    if self.indented: self.cancel_indent()
    self.marks += self.escape(content)
    return self

  #@staticmethod
  #def test():
  #  m = MarkupBuilder()
  #  m > 'html'
  #  m > 'head'
  #  m > 'title'
  #  m < 'Hello World'
  #  m <= 2
  #  m > 'body'
  #  m > 'text'
  #  with m.tag("b"):
  #    m < 'String'
  #  m >= ['a', {'id': 'str'}]
  #  m < '|sg.'
  #  m <= 4
  #  return m

  def end(self):
    ''' delimites last tag '''
    if not self.last_is_text: # cancel indentation
      #print(self.indent, self.tag_stack)
      self.cancel_indent()
      self.do_indent(False)

    self.marks += '</' + self.tag_stack.pop() + '>'
    self.do_indent(False)
    self.last_is_text = False

  # Not cared by Markup indent emitter
  def raw(self, raw):
    ''' write raw text (unescaped) '''
    self.marks += raw
    return self

  def rawtag(self, rawtext):
    ''' append unescaped raw <> text '''
    self.marks += '<'
    self.marks += rawtext
    self.marks += '>'

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

  __lt__ = text # chain
  __gt__ = begin # chain
  __add__ = raw # chain

  def __contains__(self, tag):
    ''' is tag inside enclosing tags ? '''
    return tag in self.tag_stack

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

