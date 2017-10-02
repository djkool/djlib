"""
primitives.py : Collection of geometric primitives and their mathematical interactions.

Vector - Dimensionally agnostic mathematical vector.
Point, Size - Renamed Vector for clarity.
Entity - A positioned object.
Rect - Axis Aligned Bounding Box
Circle - Radial Bounding Volume
"""
__author__ = "Andrew Peterson (DJKool14)"
__copyright__ = "Copyright 2017, DJLib Project [https://github.org/djkool/djlib]"
__credits__ = []


# IMPORTS
import math
from copy import copy

class Vector(list):

    _ATTR_STRING = "xyz"

    def __init__(self, *coords):
        list.__init__(self, list(coords))

    def __add__(self, other_vec):
        return Vector(*[x+y for x,y in zip(self, other_vec)])

    def __iadd__(self, other_vec):
        for i in xrange(len(self)):
            self[i] += other_vec[i]
        return self

    def __sub__(self, other_vec):
        return Vector(*[x-y for x,y in zip(self, other_vec)])

    def __isub__(self, other_vec):
        for i in xrange(len(self)):
            self[i] -= other_vec[i]
        return self

    def __mul__(self, vec_or_scale):
        if isinstance(vec_or_scale, Vector):
            return self.dot(vec_or_scale)
        return self.scaled(vec_or_scale)

    def __imul__(self, scale):
        for i in xrange(len(self)):
            self[i] *= scale
        return self

    def __neg__(self):
        return Vector(*[-x for x in self])

    def __eq__(self, other_vec):
        for x,y in zip(self, other_vec):
            if x != y:
                return False
        return True

    def __repr__(self):
        return "<"+", ".join(str(x) for x in self)+">"

    def __getattr__(self, attr):
        # print "get",attr
        return self[self._ATTR_STRING.index(attr)]

    def __setattr__(self, attr, value):
        # print "set",attr,value
        idx = self._ATTR_STRING.find(attr)
        if idx < 0:
            list.__setattr__(self, attr, value)
        else:
            self[idx] = value

    def __hash__(self):
        return hash(str(self))

    def length(self):
        return math.sqrt(sum([x*x for x in self]))

    def scaled(self, scale):
        return Vector(*[x*scale for x in self])

    def normalized(self):
        length = self.length()
        if length:
            return Vector(*[x/length for x in self])
        return copy(self)

    def dot(self, other_vec):
        return sum([x*y for x,y in zip(self, other_vec)])

    def args(self):
        return tuple(self)

    def intArgs(self):
        return tuple([int(x) for x in self])

    def clear(self):
        for i in xrange(len(self)):
            self[i] = 0

    def distanceApart(self, other_vec):
        return (self - other_vec).length()

    def interpolate(self, other_vec, d):
        diff = other_vec - self
        return self + diff.scaled(d)

    def copy(self):
        return copy(self)

#end Vector

class Point(Vector):
    pass
#end Point

class Size(Vector):
    _ATTR_STRING = "whl"
#end Size

class Entity(object):
    def __init__(self, position=[0,0]):
        self.pos = position

    def setPosition(self, pos):
        self.pos = pos

    def getPosition(self):
        return self.pos

    def move(self, offset):
        self.pos += offset

#end Entity

class BoundingVolume(Entity):

    def contains(self, entity):
        return self.pos == entity.pos

    def center(self):
        return self.pos

    def offset(self, offset_x, offset_y):
        return self.pos+Vector(offset_x, offset_y)

    def width(self):
        return 0

    def height(self):
        return 0

#end BoundingVolume

class Rectangle(BoundingVolume):

    # CLASS METHODS
    @classmethod
    def fromPoints(cls, top_left, bottom_right):
        return Rectangle(top_left, bottom_right - top_left)

    @classmethod
    def fromPointSize(cls, vec_pos, width, height):
        return Rectangle(vec_pos, Vector(width, height))

    @classmethod
    def fromSides(cls, left, top, right, bottom):
        return Rectangle(Vector(left, top), Vector(right-left, bottom-top))

    # INSTANCE METHODS
    def __init__(self, pos, size):
        self.pos = pos
        self.size = size

    def contains(self, entity):
        bottom_right = self.pos + self.size

        # Vector
        if isinstance(entity, Vector):
            if (entity[0] >= self.pos[0] and entity[0] <= bottom_right[0] and
                entity[1] >= self.pos[1] and entity[1] <= bottom_right[1]):
                return True
            return False
        # Rect
        elif isinstance(entity, Rectangle):
            entity_br = entity.pos + entity.size
            if (self.contains(entity.pos) and self.contains(entity_br)):
                return True
            return False
        # Circle
        elif isinstance(entity, Circle):
            if self.contains(entity.pos):
                corners = self.corners()
                for corner in corners:
                    if entity.pos.distanceApart(corner) < entity.radius:
                        return False
                return True
            return False
        raise NotImplementedError

    def center(self):
        return self.pos + self.size.scaled(0.5)

    def corners(self):
        return (self.pos.copy(), self.pos+Vector(self.size[0], 0), self.pos+Vector(0, self.size[1]), self.pos+self.size)

    def sides(self):
        return (self.pos[0], self.pos[1], self.pos[0]+self.size[0], self.pos[1]+self.size[1])

    def intersects(self, rect):
        ours = self.corners()
        for corner in ours:
            if rect.contains(corner):
                return True

        theirs = rect.corners()
        for corner in theirs:
            if self.contains(corner):
                return True
        return False

    def offset(self, offset_x, offset_y):
        o = Vector(offset_x, offset_y)
        return Rect.fromPoints(self.pos-o, self.size+o)

    def width(self):
        return self.size[0]

    def height(self):
        return self.size[1]

    def args(self):
        return (self.pos[0], self.pos[1], self.size[0], self.size[1])

    def intArgs(self):
        return (int(self.pos[0]), int(self.pos[1]), int(self.size[0]), int(self.size[1]))

    def __repr__(self):
        return "[%s-%s]" % (str(self.pos), str(self.size))

    def __getattr__(self, attr):
        if attr == "left": return self.pos[0]
        elif attr == "top": return self.pos[1]
        elif attr == "right": return self.pos[0] + self.size[0]
        elif attr == "bottom": return self.pos[1] + self.size[1]
        raise AttributeError

#end Rect

class Circle(BoundingVolume):

    # CLASS METHODS
    @classmethod
    def fromPoints(cls, center, circum):
        return Circle(center, (circum - center).length())

    @classmethod
    def fromPointSize(cls, position, radius):
        return Circle(position, radius)

    # INSTANCE METHODS
    def __init__(self, position, radius):
        BoundingVolume.__init__(self, position)
        self.radius = radius

    def pointOnCircle(self, rad):
        ray = Vector(math.cos(rad), math.sin(rad)).scaled(self.radius)
        return self.pos + ray

    def contains(self, entity):
        # Vector
        if isinstance(entity, Vector):
            return (self.pos - entity).length() <= self.radius
        # Rect
        elif isinstance(entity, Rect):
            return self.contains(entity.pos) and self.contains(entity.pos+entity.size)
        # Circle
        elif isinstance(entity, Circle):
            if self.radius > entity.radius:
                return self.pos.distanceApart(entity.pos) < (self.radius-entity.radius)
            return False

        raise NotImplementedError

    def offset(self, offset_x, offset_y):
        return Circle(self.pos, offset_x+offset_y)

    def width(self):
        return self.radius

    def height(self):
        return self.radius

#end Circle
