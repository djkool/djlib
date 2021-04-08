#!/usr/bin/env python
"""
asset.py : Basic Asset Management including Tilesets and Animations.

TileSet - Handles image that is segmented into multiple tiles of the same size.
AnimationSet - Extenstion of the TileSet that allows you to map sets of frames (tiles) to named animations.
Animator - Driver for an AnimationSet. Multiple Animators can use the same AnimationSet.
"""
__author__ = "Andrew Peterson (DJKool14)"
__copyright__ = "Copyright 2021, DJLib Project [https://github.org/djkool/djlib]"
__credits__ = []


import pygame as pg
import logging

log = logging.getLogger(__name__)


class TileSet(object):

    def __init__(self, filename, tile_size, flip_image=False):

        self.tileSize = tile_size
        self.srcTileSize = tile_size
        self.numTiles = 0
        self.tileCounts = (0,0)
        self.filename = None
        self.image = None
        self.flip_image = flip_image
        self.image_flipped = None

        self._load(filename)

    def _load(self, filename):
        self.image = pg.image.load(filename)
        assert(self.image)
        if self.image:
            self.tileCounts = (self.image.get_width()//self.tileSize[0],
                               self.image.get_height()//self.tileSize[1])
            self.numTiles = self.tileCounts[0] * self.tileCounts[1]
            self.filename = filename
            log.debug("%s tileCounts=%s, numTiles=%d", filename, str(self.tileCounts), self.numTiles)

        if self.flip_image:
            self._renderFlipped()


    def render(self, surf, pos, tile_idx, flipped=False):

        if flipped:
            assert(self.flip_image)
        
        tileRect = self.getTileRect(tile_idx)
        surf.blit(self.image if not flipped else self.image_flipped, pos, tileRect)


    def getTileRect(self, tile_idx):

        if tile_idx < 0 or tile_idx >= self.numTiles:
            raise IndexError()

        tx = tile_idx % self.tileCounts[0]
        ty = tile_idx // self.tileCounts[0]

        return pg.Rect((tx*self.tileSize[0], ty*self.tileSize[1]), self.tileSize)


    def resize(self, new_tile_size):
        new_size = (new_tile_size[0] * self.tileCounts[0], new_tile_size[1] * self.tileCounts[1])

        try:
            # Can throw if bit depth of image < 24 bits
            self.image = pg.transform.smoothscale(self.image, new_size)
            self.tileSize = new_tile_size

            if self.image_flip:
                self._renderFlipped()
        except:
            log.warn("Unable to resize TileSet to %s!", str(new_size))
            return False

        return True

    def getScale(self):
        return (float(self.tileSize[0])/self.srcTileSize[0], float(self.tileSize[1])/self.srcTileSize[1])

    def _renderFlipped(self):
        # Blit each flipped frame into the same location
        self.image_flipped = pg.Surface(self.image.get_size(), pg.SRCALPHA)
        self.image_flipped.fill((0, 0, 0, 0))
        for x in range(self.numTiles):
            fsurf = pg.transform.flip(self.image.subsurface(self.getTileRect(x)), True, False)
            self.image_flipped.blit(fsurf, self.getTileRect(x))

#end TileSet



class AnimationSet(TileSet):

    def __init__(self, filename, tile_size, image_flip=False):
        TileSet.__init__(self, filename, tile_size, image_flip)

        self.anims = {}

    def addAnim(self, name, start_frame, end_frame):

        if name in self.anims or start_frame > end_frame:
            return False

        self.anims[name] = (start_frame, end_frame)
        return True

    def getAnim(self, name):
        return self.anims.get(name)

#end Animation



class Animator(object):

    MODE_STOPPED = 0
    MODE_PLAYONCE = 1
    MODE_LOOP = 2
    MODE_PINGPONG = 3
    MODE_PING = 3
    MODE_PONG = 4

    def __init__(self, animation_set, mode = 2, fps = 1.0):

        self.animset = animation_set
        self.mode = mode
        self.period = 1.0/fps
        self.frame = 0
        self.time = 0.0
        self.anim = (0, self.animset.numTiles-1)

    def update(self, dt):
        if self.mode == Animator.MODE_STOPPED:
            return

        self.time += dt
        if self.time > self.period:
            self.time -= self.period
            self.next()


    def next(self):
        anim = self.anim if self.anim else (0, self.animset.numTiles-1)
        if self.mode == Animator.MODE_PONG:
            self.frame -= 1
            if self.frame == anim[0]:
                self.mode = Animator.MODE_PING
        elif self.mode != Animator.MODE_STOPPED:
            self.frame += 1
            if self.frame >= anim[1]:
                if self.mode == Animator.MODE_PLAYONCE:
                    self.mode = Animator.MODE_STOPPED
                elif self.mode == Animator.MODE_PING:
                    self.mode = Animator.MODE_PONG
                elif self.frame > anim[1]: #MODE_LOOP
                    self.frame = anim[0]


    def setAnim(self, name, mode = -1):
        anim = self.animset.getAnim(name)

        if anim != self.anim:
            self.anim = anim
            if mode >= 0:
                self.mode = mode

            self.frame = self.anim[1] if self.mode == Animator.MODE_PONG else self.anim[0]
            log.debug("anim set %s", str(anim))


    def render(self, surf, pos, flipped=False):
        self.animset.render(surf, pos, self.frame, flipped)


    def finished(self):
        return self.mode == Animator.MODE_STOPPED

    def setFrame(self, index):
        """ Set current frame based on offset within the current Animation """
        frame = self.anim[0] + index
        if frame > self.anim[1]:
            return False

        self.frame = frame
        return True

#end Animator
