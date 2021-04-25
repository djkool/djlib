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

from sys import getsizeof
from itertools import chain
from collections import deque, defaultdict
import logging
import pprint

import pygame as pg

from djlib.utils import Singleton


log = logging.getLogger(__name__)

class AssetManager(Singleton):

    class AssetStack(object):
        def __init__(self):
            self.assets = defaultdict(lambda: {})
            self.size = 0

        def dumpInfo(self):
            log.debug("\nAssets:\n%s", pprint.pformat(self.assets, indent=4))
            log.debug("Size: %i", self.size)

    # end AssetStack


    def init(self, cache_assets = True):
        self.cache_assets = cache_assets
        self.managing = {}
        self.asset_stack = [AssetManager.AssetStack()]
        self.curr = self.asset_stack[0]
        self.tsize = 0

        self._managed_loaders = {}

        # Install known loaders
        self.manage(pg.Surface, pg.image, "Image")
        self.manage(TileSet)
        self.manage(AnimationSet)

    def manage(self, asset_class, loader=None, name=None):
        loader = loader if loader else asset_class
        name = name if name else asset_class.__name__
        if asset_class in self.managing:
            log.warn("%s is already being managed.", name)
            return False

        # create loading function
        def _load(filename, *args, **kargs):
            asset = self.getAsset(filename, asset_class)
            if asset:
                log.debug("Loading %s from cache.", filename)
                return asset

            log.debug("Loading %s(%s)-%s into AssetManager.", name, str(asset_class), filename)
            asset = loader.load(filename, *args, **kargs)
            self.trackAsset(filename, asset)
            return asset

        self._managed_loaders[name] = asset_class
        self.managing[asset_class] = _load
        return True

    def trackAsset(self, filename, asset):
        """ Track Assets not loaded by AssetManager."""
        if not self.cache_assets:
            return False

        assets = self.curr.assets[asset.__class__]
        if not assets.get(filename, None):
            assets[filename] = asset
            size = self._trackSize(asset)
            log.debug("Tracking %s(%s)-%s Size(%i):%s", asset.__class__.__name__, str(asset.__class__), filename, size, str(asset))
            return True
        return False

    def getAsset(self, filename, asset_class=None):
        if asset_class:
            assets = self.curr.assets[asset_class]
            return assets.get(filename, None)

        for assets in self.curr.assets.values():
            asset = assets.get(filename, None)
            if asset:
                return asset
        return None

    def saveAssets(self):
        # Create new stack object
        idx = len(self.asset_stack)
        self.asset_stack.append(AssetManager.AssetStack())
        self.curr = self.asset_stack[idx]

        log.info("Saving asset stack %i...", idx)
        return len(self.asset_stack)

    def restoreAssets(self):
        assets = self.asset_stack.pop()
        idx = len(self.asset_stack)
        self.curr = self.asset_stack[idx-1]

        log.info("Restoring stack %i:", idx)
        assets.dumpInfo()
        return idx

    def dumpDebug(self):
        log.debug("\nLoaders:\n%s", pprint.pformat(self._managed_loaders, indent=4))
        log.debug("Asset Stacks(%d):", len(self.asset_stack))
        for assets in self.asset_stack:
            assets.dumpInfo()
        log.debug("Total Size: %i bytes.", self.tsize)


    # Attempt to track assets sizes
    # Credit: https://code.activestate.com/recipes/577504/
    def total_size(o, handlers={}, verbose=False):
        """ Returns the approximate memory footprint an object and all of its contents.

        Automatically finds the contents of the following builtin containers and
        their subclasses:  tuple, list, deque, dict, set and frozenset.
        To search other containers, add handlers to iterate over their contents:

            handlers = {SomeContainerClass: iter,
                        OtherContainerClass: OtherContainerClass.get_elements}

        """
        dict_handler = lambda d: chain.from_iterable(d.items())
        all_handlers = {tuple: iter,
                        list: iter,
                        deque: iter,
                        dict: dict_handler,
                        set: iter,
                        frozenset: iter,
                       }
        all_handlers.update(handlers)     # user handlers take precedence
        seen = set()                      # track which object id's have already been seen
        default_size = getsizeof(0)       # estimate sizeof object without __sizeof__

        def sizeof(o):
            if id(o) in seen:       # do not double count the same object
                return 0
            seen.add(id(o))
            s = getsizeof(o, default_size)

            if verbose:
                log.debug(s, type(o), repr(o))

            for typ, handler in all_handlers.items():
                if isinstance(o, typ):
                    s += sum(map(sizeof, handler(o)))
                    break
            return s

        return sizeof(o)

    def _trackSize(self, asset):
        size = getsizeof(asset)
        self.curr.size += size
        self.tsize += size
        return size

    def _load(self, filename, *args, **kargs):
        pass

    # Override getattr to catch and redirect load calls
    def __getattr__(self, attr):
        # LOAD - load<CLASS>
        if attr.startswith("load"):
            classname = attr[4:]
            if not classname in self._managed_loaders:
                raise TypeError("%s is not a managed asset class. Use AssetManager.manage() to track." % classname)
            asset_class = self._managed_loaders[classname]
            return self.managing[asset_class]
        # GET - get<CLASS>
        elif attr.startswith("get") and attr != "getAsset":
            classname = attr[3:]
            if not classname in self._managed_loaders:
                raise TypeError("%s is not a managed asset class. Use AssetManager.manage() to track." % classname)
            asset_class = self._managed_loaders[classname]
            log.debug("%s(%s):%s", classname, str(asset_class), str(self.curr.assets[asset_class]))
            return lambda filename: self.getAsset(filename, asset_class)

        # Pass other attrs to default handler
        return object.__getattr__(self, attr)

#end AssetManager



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
