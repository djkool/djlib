"""
primitives.py : Collection of geometric primitives and their mathematical interactions.

Vector - Dimensionally agnostic mathematical vector.
Point, Size - Renamed Vector for clarity.
Entity - A positioned object.
Rect - Axis Aligned Bounding Box
Circle - Radial Bounding Volume
"""
__author__ = "Andrew Peterson (DJKool14)"
__copyright__ = "Copyright 2021, DJLib Project [https://github.org/djkool/djlib]"
__credits__ = []


# IMPORTS
import math


class Vector(list):

    _ATTR_STRING = "xyz"

    def __init__(self, *coords):
        list.__init__(self, list(coords))

    def __add__(self, other_vec):
        return Vector(*[x+y for x,y in zip(self, other_vec)])

    def __iadd__(self, other_vec):
        for i in range(len(self)):
            self[i] += other_vec[i]
        return self

    def __sub__(self, other_vec):
        return Vector(*[x-y for x,y in zip(self, other_vec)])

    def __isub__(self, other_vec):
        for i in range(len(self)):
            self[i] -= other_vec[i]
        return self

    def __mul__(self, vec_or_scale):
        if isinstance(vec_or_scale, Vector):
            return self.dot(vec_or_scale)
        return self.scaled(vec_or_scale)

    def __imul__(self, scale):
        for i in range(len(self)):
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
        if attr in self._ATTR_STRING:
            return self[self._ATTR_STRING.index(attr)]
        return list.__getattr__(attr)

    def __setattr__(self, attr, value):
        # print "set",attr,value
        idx = self._ATTR_STRING.find(attr)
        if idx < 0:
            list.__setattr__(self, attr, value)
        else:
            self[idx] = value

    def __hash__(self):
        return hash(str(self))

    def set(self, *coords):
        assert(len(coords) == len(self))
        for i, v in enumerate(coords):
            self[i] = v

    def length(self):
        return math.sqrt(sum([x*x for x in self]))

    def empty(self):
        return not any(self)

    def scaled(self, scale):
        return Vector(*[x*scale for x in self])

    def normalized(self):
        length = self.length()
        if length:
            return Vector(*[x/length for x in self])
        return self.copy()

    def intify(self):
        return Vector(*self.intArgs())

    def dot(self, other_vec):
        return sum([x*y for x,y in zip(self, other_vec)])

    def args(self):
        return tuple(self)

    def intArgs(self):
        return tuple([int(x) for x in self])

    def clear(self):
        for i in range(len(self)):
            self[i] = 0

    def distanceApart(self, other_vec):
        return (self - other_vec).length()

    def interpolate(self, other_vec, d):
        diff = other_vec - self
        return self + diff.scaled(d)

    def copy(self):
        return Vector(*self)

#end Vector


class Point(Vector):
    pass
#end Point


class Size(Vector):
    _ATTR_STRING = "whl"
#end Size


class Entity(object):
    def __init__(self, position=Point(0, 0)):
        self.pos = position

    def setPosition(self, x, y=None):
        # API changed, so still handle passing of a single argument
        if y is None:
            self.pos = x if isinstance(x, Vector) else Vector(*x)
        else:
            self.pos.set(x, y)

    def getPosition(self):
        return self.pos

    def move(self, offset):
        self.pos += offset

#end Entity


class Ray(Entity):
    from math import pi as PI
    RAD_DEGREES = 360 / math.tau

    # CLASS CONSTRUCTOR HELPERS
    @classmethod
    def fromPoints(cls, pos, opos):
        return Ray(pos, opos - pos)

    def __init__(self, pos, dir_):
        Entity.__init__(self, pos)
        self.dir = dir_

    def set(self, pos, dir_):
        self.pos = pos
        self.dir = dir_

    def size(self):
        return self.dir.length()

    def length(self):
        return self.dir.length()

    def angle(self, radians=False):
        rot = math.atan2(self.dir.y, self.dir.x) + self.PI
        return rot if radians else radians * self.RAD_DEGREES

    def rotateDeg(self, degrees):
        self.rotateRad(degrees / self.RAD_DEGREES)

    def rotateRad(self, rads):
        self.dir.x = self.dir.x*math.cos(rads) - self.dir.y*math.sin(rads)
        self.dir.y = self.dir.x*math.sin(rads) + self.dir.y*math.cos(rads)

    def endPoint(self):
        return self.pos + self.dir

#end Ray


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

    def size(self):
        return (self.width(), self.height())

    def args(self):
        return self.pos.args()

    def intArgs(self):
        return self.pos.intArgs()

#end BoundingVolume


class Rectangle(BoundingVolume):

    # CLASS METHODS
    @classmethod
    def fromPoints(cls, top_left, bottom_right):
        return Rectangle(top_left, bottom_right - top_left)

    @classmethod
    def fromPosSize(cls, x, y, width, height):
        return Rectangle(Vector(x, y), Vector(width, height))

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

    def __add__(self, vector):
        assert(isinstance(vector, Vector))
        return Rectangle.fromPointSize(self.pos + vector, *self.size)

    def __sub__(self, vector):
        assert(isinstance(vector, Vector))
        return Rectangle.fromPointSize(self.pos - vector, *self.size)

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
        # Entity - Keep last
        elif isinstance(entity, Entity):
            return self.contains(entity.pos)

        print("Unknown Entity - %s" % str(entity))
        raise NotImplementedError

    def center(self):
        return self.pos + self.size.scaled(0.5)

    def corners(self):
        return (self.pos.copy(), self.pos+Vector(self.size[0], 0), self.pos+Vector(0, self.size[1]), self.pos+self.size)

    def sides(self):
        return (self.pos[0], self.pos[1], self.pos[0]+self.size[0], self.pos[1]+self.size[1])

    def intersect(self, rect):
        if not self.intersects(rect):
            return None

        return Rectangle.fromSides(self.left if self.left >= rect.left else rect.left,
                                   self.top if self.top >= rect.top else rect.top,
                                   self.right if self.right < rect.right else rect.right,
                                   self.bottom if self.bottom < rect.bottom else rect.bottom)

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

    def __add__(self, vector):
        assert(isinstance(vector, Vector))
        return Circle.fromPointSize(self.pos + vector, self.radius)

    def __sub__(self, vector):
        assert(isinstance(vector, Vector))
        return Circle.fromPointSize(self.pos - vector, self.radius)

    def pointOnCircle(self, rad):
        ray = Vector(math.cos(rad), math.sin(rad)).scaled(self.radius)
        return self.pos + ray

    def contains(self, entity):
        # Vector
        if isinstance(entity, Vector):
            return (self.pos - entity).length() <= self.radius
        # Rect
        elif isinstance(entity, Rectangle):
            return self.contains(entity.pos) and self.contains(entity.pos+entity.size)
        # Circle
        elif isinstance(entity, Circle):
            if self.radius > entity.radius:
                return self.pos.distanceApart(entity.pos) < (self.radius-entity.radius)
            return False
        #Entity - Keep last
        elif isinstance(entity, Entity):
            return self.contains(entity.pos)

        print("Unknown Entity - %s" % str(entity))
        raise NotImplementedError

    def offset(self, offset):
        return Circle(self.pos, offset)

    def width(self):
        return self.diameter()

    def height(self):
        return self.diameter()

    def diameter(self):
        return self.radius * 2

    def args(self):
        return (self.pos.args(), self.radius)

    def intArgs(self):
        return (self.pos.intArgs(), int(self.radius))

#end Circle
