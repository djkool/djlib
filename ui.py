#!/usr/bin/env python
"""
ui.py : Basic UI Framework

"""
__author__ = "Andrew Peterson (DJKool14)"
__copyright__ = "Copyright 2021, DJLib Project [https://github.org/djkool/djlib]"
__credits__ = []


import string

import pygame as pg
from pygame.locals import *

from .primitives import Rectangle as Rect



class Events:
    """
    Custom Event IDs used when pushing custom USEREVENTS through
    the pygame events queue instead of direct callback notifications.
    """

    START_ID = 1234,
    BUTTON_CLICKED = 1234
    EDITBOX_RETURN = 1235

    END_ID = 1236
#end Event


class Theme(object):
    """
    Base Theme acting as a Base Class for all other themes.
    """

    # Various Flags
    F_NONE = 0
    F_CENTER_HORZ = 1
    F_CENTER_VERT = 2
    F_CENTER_FULL = 3
    F_PAD_HORZ = 4
    F_PAD_VERT = 8
    F_PAD_FULL = 12

    FONT = None # Delay font creation until first text
    FONT_COLOR = pg.Color(255, 255, 255)

    PADDING = 0 

    def drawFrame(self, surf, rect):
        raise NotImplemented()

    def drawButton(self, surf, rect, state):
        raise NotImplemented()

    def drawText(self, surf, rect, text, flags=0):
        if not self.FONT:
            self.FONT = pg.font.Font(pg.font.get_default_font(), 12)

        text_surf = self.FONT.render(text, False, self.FONT_COLOR)

        if flags & Theme.F_PAD_FULL:
            rect = rect.inflate(-self.PADDING if flags & self.F_PAD_HORZ else 0,
                                -self.PADDING if flags & self.F_PAD_VERT else 0)
        pos = rect.topleft
        if flags & Theme.F_CENTER_FULL:
            pos = (pos[0] + ((rect.width-text_surf.get_width())/2 if flags & self.F_CENTER_HORZ else 0),
                   pos[1] + ((rect.height-text_surf.get_height())/2 if flags & self.F_CENTER_VERT else 0))

        surf.blit(text_surf, pos)
        return text_surf.get_width()

#end Theme


class ColorTheme(Theme):

    # Frame Colors
    BG_COLOR = pg.Color(255, 0, 0)
    FG_COLOR = pg.Color(255, 255, 0)

    # Button Colors (UP, HOVER, DOWN)
    BUT_COLORS = ( FG_COLOR, pg.Color(192, 192, 0), pg.Color(128, 128, 0) )
    BEV_SIZES  = ( 1, 2, 4)
    BEV_COLOR = pg.Color(0, 255, 255)

    PADDING = 4

    def drawFrame(self, surf, rect):
        pg.draw.rect(surf, self.BG_COLOR, rect, 0)

    def drawButton(self, surf, rect, state):
        pg.draw.rect(surf, self.BUT_COLORS[state], rect, 0)
        pg.draw.rect(surf, self.BEV_COLOR, rect, self.BEV_SIZES[state])

#end ColorTheme


_THEME = ColorTheme()

def setTheme(theme):
    global _THEME
    if theme != _THEME:
        _THEME = theme

#end setTheme


class Frame(object):

    def __init__(self, bounds):
        self.parent = None
        self.visible = True
        self.bounds = pg.Rect(*bounds)
        self.children = []

    def render(self, surf):
        if not self.visible:
            return

        _THEME.drawFrame(surf, self.getRect())
        if self.children:
            for c in self.children:
                if c.visible:
                    c.render(surf)

    def processEvent(self, event):
        # Only mouse events 
        if hasattr(event, 'pos') and not self.getRect().collidepoint(event.pos):
            return False
        return self._delegate('processEvent', event)

    def getRect(self):
        return self.bounds.move(*self.parent.bounds.topleft) if self.parent else self.bounds

    def addChild(self, child):
        assert(isinstance(child, Frame))
        self.children.append(child)
        child.parent = self

    def _delegate(self, call, *args, **kargs):
        if not self.children:
            return False
        for c in self.children:
            if getattr(c, call)(*args, **kargs):
                return True
        return False

#end Frame



class Text(Frame):

    def __init__(self, bounds, text="", centered = False):
        Frame.__init__(self, bounds)
        self.text = text
        self.flags = Theme.F_CENTER_FULL if centered else 0

    def render(self, surf):
        _THEME.drawText(surf, self.getRect(), self.text, self.flags)

    def processEvent(self, event):
        return False

#end Text



class Button(Frame):

    UP = 0
    HOVER = 1
    DOWN = 2

    def __init__(self, bounds, text, callback = None):
        Frame.__init__(self, bounds)
        self.text = text
        self.callback = callback
        self.state = Button.UP

    def render(self, surf):
        _THEME.drawButton(surf, self.getRect(), self.state)
        _THEME.drawText(surf, self.getRect(), self.text, Theme.F_CENTER_FULL)

    def processEvent(self, event):
        # Moving into or out of button
        if event.type == MOUSEMOTION:
            if self.getRect().collidepoint(event.pos):
                if not self.state == Button.DOWN:
                    self._changeState(Button.HOVER)
                    return True
            elif not self.state == Button.UP:
                self._changeState(Button.UP)
        elif self.state == Button.HOVER:
            # If state is already HOVER, always assume mouse is in Rect
            if event.type == MOUSEBUTTONDOWN:
                self._changeState(Button.DOWN)
                return True
        elif self.state == Button.DOWN:
            if event.type == MOUSEBUTTONUP:
                self._changeState(Button.HOVER)
                return True
        return False

    def _changeState(self, new_state):
        if self.state == new_state:
            return

        if self.state == Button.HOVER:
            if new_state == Button.DOWN:
                self._notify()

        self.state = new_state

    def _notify(self):
        if self.callback:
            self.callback(self)
        else:
            pg.event.post(pg.event.Event(USEREVENT, usercode=Events.BUTTON_CLICKED, wnd=self))

#end Button


class CheckBox(Button):

    def __init__(self, bounds, text, callback=None):
        Button.__init__(self, bounds, text, callback)
        self.checked = False

    def render(self, surf):
        rect = self.getRect()
        check_rect = pg.Rect(rect.topleft, (rect.height, rect.height))
        state = Button.DOWN if self.checked else self.state
        _THEME.drawButton(surf, check_rect, state)
        if self.checked:
            _THEME.drawText(surf, check_rect, "X", Theme.F_CENTER_FULL)
        rect = pg.Rect(check_rect.topright, (rect.width-check_rect.width, rect.height))
        _THEME.drawText(surf, rect, self.text, Theme. F_CENTER_VERT)

#end CheckBox


class EditBox(Frame):

    def __init__(self, bounds, text=""):
        Frame.__init__(self, bounds)
        self.text = text
        self.focused = False
        self.selPos = 0

    def render(self, surf):
        text = self.text
        if self.focused:
            text = self.text[:self.selPos]+"|"+self.text[self.selPos:]
        _THEME.drawButton(surf, self.getRect(), Button.DOWN)
        _THEME.drawText(surf, self.getRect(), text, Theme.F_CENTER_VERT | Theme.F_PAD_HORZ)

    def processEvent(self, event):
        if event.type == MOUSEBUTTONDOWN:
            if self.getRect().collidepoint(event.pos):
                self.focused = True
                self.selPos = len(self.text)
            else:
                self.focused = False

        elif event.type == KEYDOWN:
            if not self.focused:
                return False

            if event.key == K_LEFT:
                self.selPos -= 1 if self.selPos > 0 else 0
            elif event.key == K_RIGHT:
                self.selPos += 1 if self.selPos < len(self.text) else 0
            elif event.key == K_BACKSPACE and self.selPos > 0:
                self.selPos -= 1
                self.text = self.text[:self.selPos]+self.text[self.selPos+1:]
            elif event.key == K_RETURN:
                pg.event.post(pg.event.Event(USEREVENT, usercode=Events.EDITBOX_RETURN, wnd=self))
            elif event.unicode and event.unicode in string.printable:
                self.text = self.text[:self.selPos]+event.unicode+self.text[self.selPos:]
                self.selPos += 1
            return True

    def setFocus(self, focus):
        self.focused = focus

#end EditBox
