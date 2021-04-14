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

from djlib.utils import enum, flags
import logging

log = logging.getLogger(__name__)


"""
Custom Event IDs used when pushing custom USEREVENTS through
the pygame events queue instead of direct callback notifications.
"""
Events = enum(
    START_ID = 1234,
    BUTTON_CLICKED = 1234,
    EDITBOX_RETURN = 1235,

    END_ID = 1236
)

class Theme(object):
    """
    Base Theme acting as a Base Class for all other themes.
    """

    # Various Flags
    Format = flags(
        "NONE",
        "CENTER_HORZ",
        "CENTER_VERT",
        "CENTER_FULL",
        "PAD_HORZ",
        "PAD_VERT",
        "PAD_FULL",
    )

    FONT = None # Delay font creation until first text
    FONT_COLOR = pg.Color(255, 255, 255)
    FONT_SIZE = 12

    PADDING = 0 

    def drawFrame(self, surf, rect):
        raise NotImplemented()

    def drawButton(self, surf, rect, state):
        raise NotImplemented()

    def drawImage(self, surf, rect, image):
        raise NotImplemented()

    def drawInput(self, surf, rect):
        raise NotImplemented()

    def drawProgress(self, surf, rect, progress, steps):
        raise NotImplemented()

    def drawText(self, surf, rect, text, flags=0):
        if not self.FONT:
            self.FONT = pg.font.Font(pg.font.get_default_font(), self.FONT_SIZE)

        text_surf = self.FONT.render(text, True, self.FONT_COLOR)

        if flags & Theme.Format.PAD_FULL:
            rect = rect.inflate(-self.PADDING if flags & self.Format.PAD_HORZ else 0,
                                -self.PADDING if flags & self.Format.PAD_VERT else 0)
        pos = rect.topleft
        if flags & Theme.Format.CENTER_FULL:
            pos = (pos[0] + ((rect.width-text_surf.get_width())/2 if flags & self.Format.CENTER_HORZ else 0),
                   pos[1] + ((rect.height-text_surf.get_height())/2 if flags & self.Format.CENTER_VERT else 0))

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

    PB_COLOR = pg.Color(255, 255, 255)
    PB_BORDER = 2

    def drawFrame(self, surf, rect):
        pg.draw.rect(surf, self.BG_COLOR, rect, 0)

    def drawButton(self, surf, rect, state):
        pg.draw.rect(surf, self.BUT_COLORS[state], rect, 0)
        pg.draw.rect(surf, self.BEV_COLOR, rect, self.BEV_SIZES[state])

    def drawImage(self, surf, rect, image):
        surf.blit(image, rect)

    def drawInput(self, surf, rect):
        self.drawButton(surf, rect, Button.DOWN)

    def drawProgress(self, surf, rect, progress, steps):
        fprogress = float(progress)/steps
        prect = pg.Rect(rect.x, rect.y, rect.width * fprogress, rect.height)
        pg.draw.rect(surf, self.PB_COLOR, rect, self.PB_BORDER)
        pg.draw.rect(surf, self.PB_COLOR, prect, 0)

#end ColorTheme


_THEME = ColorTheme()

def setTheme(theme):
    global _THEME
    if theme != _THEME:
        _THEME = theme

#end setTheme


class Frame(object):

    def __init__(self, bounds):
        self.bounds = bounds.copy() if isinstance(bounds, pg.Rect) else pg.Rect(*bounds)
        self.parent = None
        self.visible = True
        self.dirty = True
        #self.children = []

    def render(self, surf):
        self.dirty = False
        if not self.visible:
            return

        _THEME.drawFrame(surf, self.getRect())
        self._delegate('render', surf)

    def processEvent(self, event):
        # Only mouse events 
        if hasattr(event, 'pos') and not self.getRect().collidepoint(event.pos):
            return False
        return self._delegate('processEvent', event)

    def getRect(self):
        return self.bounds.move(*self.parent.getRect().topleft) if self.parent else self.bounds

    def addChild(self, child):
        assert(isinstance(child, Frame))
        if not hasattr(self, 'children'):
            self.children = []
        self.children.append(child)
        child.parent = self
        return child

    def redraw(self):
        self.dirty = True
        if self.parent:
            self.parent.redraw()

    def _delegate(self, call, *args, **kargs):
        if hasattr(self, 'children') and self.children:
            for c in self.children:
                if getattr(c, call)(*args, **kargs):
                    return True
        return False

    def _debugTree(self, depth = 0):
        log.debug("%s %s" % ("\t" * depth, str(self)))
        self._delegate('_debugTree', depth+1)

#end Frame



class Text(Frame):

    def __init__(self, bounds, text="", centered = False):
        Frame.__init__(self, bounds)
        self.text = text
        self.flags = Theme.Format.CENTER_FULL if centered else 0

    def setText(self, text):
        if text != self.text:
            self.text = text
            self.redraw()

    def render(self, surf):
        _THEME.drawText(surf, self.getRect(), self.text, self.flags)

    def processEvent(self, event):
        return False

#end Text


class Image(Frame):

    def __init__(self, bounds, image, keep_ratio=True):
        Frame.__init__(self, bounds)
        self.image = None
        if image:
            self.setImage(image, keep_ratio)

    def setImage(self, image, keep_ratio=True):
        if self.image == image:
            return

        new_size = self.bounds.size
        if keep_ratio:
            img_ratio = float(image.get_width()) / image.get_height()
            bnd_ratio = float(self.bounds.width) / self.bounds.height

            if img_ratio > bnd_ratio:
                new_size = (self.bounds.width, int(self.bounds.width / img_ratio))
            else:
                new_size = (int(self.bounds.height * img_ratio), self.bounds.height)

        self.image = image
        if new_size[0] != image.get_width() or new_size[1] != image.get_height():
            self.image = pg.transform.scale(image, new_size)
        self.redraw()

    def render(self, surf):
        if self.image:
            _THEME.drawImage(surf, self.getRect(), self.image)

# end Image


class Button(Frame):

    UP = 0
    HOVER = 1
    DOWN = 2

    def __init__(self, bounds, text, callback = None, key = None):
        Frame.__init__(self, bounds)
        self.text = text
        self.callback = callback
        self.state = Button.UP
        self.key = key

    def render(self, surf):
        _THEME.drawButton(surf, self.getRect(), self.state)
        _THEME.drawText(surf, self.getRect(), self.text, Theme.Format.CENTER_FULL)

    def processEvent(self, event):
        # Moving into or out of button
        if event.type == MOUSEMOTION:
            if self.getRect().collidepoint(event.pos):
                if not self.state == Button.DOWN:
                    self._changeState(Button.HOVER)
                    return True
            elif not self.state == Button.UP:
                self._changeState(Button.UP)
        elif event.type == KEYDOWN and event.key == self.key:
            self._changeState(Button.DOWN)
        elif self.state == Button.HOVER:
            # If state is already HOVER, always assume mouse is in Rect
            if event.type == MOUSEBUTTONDOWN:
                self._changeState(Button.DOWN)
                return True
        elif self.state == Button.DOWN:
            if event.type == MOUSEBUTTONUP:
                self._changeState(Button.HOVER)
                return True
            elif event.type == KEYUP and event.key == self.key:
                self._changeState(Button.UP)
                return True

        return False

    def _changeState(self, new_state):
        if self.state == new_state:
            return

        if self.state == Button.DOWN:
            if new_state in (Button.UP, Button.HOVER):
                self._notify()

        self.state = new_state
        self.redraw()

    def _notify(self):
        if self.callback:
            self.callback(self)
        else:
            pg.event.post(pg.event.Event(USEREVENT, usercode=Events.BUTTON_CLICKED, wnd=self))

#end Button


class ImageButton(Button):

    def __init__(self, bounds, name, image, callback=None, key=None, image_hover=None, image_down=None):
        Button.__init__(self, bounds, name, callback, key)
        self.images = {}
        self.setImages(image, image_hover, image_down)

    def setImages(self, image_up, image_hover=None, image_down=None):
        self.images[Button.UP] = image_up
        self.images[Button.HOVER] = image_hover
        self.images[Button.DOWN] = image_down

    def render(self, surf):
        img = self.images.get(self.state)
        _THEME.drawImage(surf, self.getRect(), img if img else self.images[Button.UP])

# end ImageButton


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
            _THEME.drawText(surf, check_rect, "X", Theme.Format.CENTER_FULL)
        rect = pg.Rect(check_rect.topright, (rect.width-check_rect.width, rect.height))
        _THEME.drawText(surf, rect, self.text, Theme.Format.CENTER_VERT)

#end CheckBox


class EditBox(Frame):

    def __init__(self, bounds, text="", callback=None):
        Frame.__init__(self, bounds)
        self.text = text
        self.focused = False
        self.callback = callback
        self.selPos = 0

    def render(self, surf):
        text = self.text
        if self.focused:
            text = self.text[:self.selPos]+"|"+self.text[self.selPos:]
        _THEME.drawInput(surf, self.getRect())
        _THEME.drawText(surf, self.getRect(), text, Theme.Format.CENTER_VERT | Theme.Format.PAD_HORZ)

    def processEvent(self, event):
        if event.type == MOUSEBUTTONDOWN:
            if self.getRect().collidepoint(event.pos):
                self.selPos = len(self.text)
                self.setFocus(True)
            else:
                self.setFocus(False)

        elif event.type == KEYDOWN:
            if not self.focused:
                return False

            if event.key == K_LEFT:
                self.setCursor(self.selPos - 1)
            elif event.key == K_RIGHT:
                self.setCursor(self.selPos + 1)
            elif event.key == K_BACKSPACE and self.selPos > 0:
                self.selPos -= 1
                self.setText(self.text[:self.selPos]+self.text[self.selPos+1:])
            elif event.key == K_RETURN:
                self._notify()
            elif event.unicode and event.unicode in string.printable:
                self.text = self.text[:self.selPos]+event.unicode+self.text[self.selPos:]
                self.selPos += 1
                self.redraw()
            return True

    def setText(self, text):
        if text == self.text:
            return

        self.text = text
        if self.focused and self.selPos > len(self.text):
            self.selPos = len(self.text)
        self.redraw()

    def setFocus(self, focus):
        if focus != self.focused:
            self.focused = focus
            if focus:
                self.selPos = len(self.text)
            self.redraw()

    def setCursor(self, pos):
        # Bounds Check
        if pos < 0:
            pos = 0
        elif pos > len(self.text):
            pos = len(self.text)

        if pos != self.selPos:
            self.selPos = pos
            self.redraw()

    def _notify(self):
        if self.callback:
            self.callback(self)
        else:
            pg.event.post(pg.event.Event(USEREVENT, usercode=Events.EDITBOX_RETURN, frame=self))

#end EditBox

class ProgressBar(Frame):

    def __init__(self, bounds, steps):
        Frame.__init__(self, bounds)
        self.steps = steps
        self.progress = 0

    def render(self, surf):
        _THEME.drawProgress(surf, self.bounds, self.progress, self.steps)

#end ProgressBar


class View(Frame):

    def __init__(self, bounds, background = None):
        Frame.__init__(self, bounds)
        self.surf = pg.Surface(self.bounds.size)
        self.bg = background
        if background.get_width() != self.bounds.width or background.get_height() != self.bounds.height:
            self.bg = pg.transform.scale(background, self.bounds.size)
        self.dirty = True

    def render(self, surf):
        # Don't render if not visible, but keep dirty status
        if not self.visible:
            return

        if self.dirty:
            self.dirty = False
            tb = self.bounds
            self.bounds = pg.Rect(0, 0, tb.width, tb.height)
            if self.bg:
                _THEME.drawImage(self.surf, self.bounds, self.bg)
            else:
                _THEME.drawFrame(self.surf, self.bounds)

            self._delegate('render', self.surf)

            self.bounds = tb

        if surf:
            surf.blit(self.surf, self.getRect().topleft)

    def getCoords(self, sx, sy):
        return (int(self.bounds.width * sx), int(self.bounds.height * sy))

#end View
