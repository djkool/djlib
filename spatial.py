#!/usr/bin/env python
"""
spatial.py : Some spatial tracking structures

"""
__author__ = "Andrew Peterson (DJKool14)"
__copyright__ = "Copyright 2017, DJLib Project [https://github.org/djkool/djlib]"
__credits__ = []


from .primitives import Point, Rect

class QuadTree:

    NUM_CHILDREN = 4
    MAX_DATA = 10

    def __init__(self):
        self.children = None
        self.data = None

    def insert(self, data):
        # Leaf nodes have no children
        if not self.children:
            # no existing data
            if not self.data:
                self.data = [data]
                return self

            # add to existing data if node isn't full
            if len(self.data) < self.MAX_DATA:
                self.data.append(data)
                return self

            # this node is full, create children
            self.children = self._createChildren()

            # child won't get created if certain conditions are met
            if not self.children:
                #override MAX_DATA rule at this point
                self.data.append(data)
                return self;

            # move existing data to the new children
            for d in self.data:
                self.children[self._childIndex(d)].insert(d)
            self.data = None

        # If we got this far, Children have to exist
        return self.children[self._childIndex(data)].insert(data)


    def remove(self, data):
        # Leaf nodes have no children
        if not self.children:
            if not self.data:
                return #not found, should this be an error?

            self.data.remove(data)
            if len(self.data) == 0:
                self.data = None
        else: #recurse children
            self.children[self._childIndex(data)].remove(data)

            # See if our children are empty
            rem = True
            for child in self.children:
                if not child.empty():
                    rem = False
                    break

            # remove uneeded children
            if rem:
                self.children = None

    def empty(self):
        return not self.children and not self.data

    def count(self):
        if self.data:
            return len(self.data)
        
        c = 0
        if self.children:
            for child in self.children:
                c += child.count()
        return c

    def _childIndex(self, data):
        return 0

    def _createChildren(self):
        return [QuadTree()] * self.NUM_CHILDREN

    def __iter__(self):
            if self.data:
                for d in self.data:
                    yield d

            if self.children:
                for child in self.children:
                    for d in child:
                        yield d

#end QuadTree

class RectTree(QuadTree):

    MIN_RECT = Rect.fromSides(0, 0, 250, 250)

    def __init__(self, rect):
        QuadTree.__init__(self)
        self.rect = rect

    def minNode(self, bounds_rect):

        if not self.rect.contains(bounds_rect):
            return None

        node = None
        if self.children:
            for child in self.children:
                node = child.minNode(bounds_rect)
                if node:
                    return node

        return self

    def getData(self, bounds_rect = None):
        if bounds_rect and not bounds_rect.intersects(self.rect):
            return []

        if self.data:
            return self.data

        data = []
        if self.children:
            data = []
            for child in self.children:
                data.extend(child.getData(bounds_rect))

        return data

        
    def _childIndex(self, entity):
        pos = entity.getPosition()
        center = self.rect.center()
        return (0 if pos.x < center.x else 1) + 2*(0 if pos.y < center.y else 1)

    def _createChildren(self):
        pos = self.rect.getPosition()
        center = self.rect.center()
        size = center - pos

        # child rect can't be smaller than MIN_SIZE to prevent infinite recursion.
        if self.MIN_RECT.contains(size):
            return None

        return [ RectTree(Rect(pos, size)),
                 RectTree(Rect(pos + Point(size.x, 0), size)),
                 RectTree(Rect(pos + Point(0, size.y), size)),
                 RectTree(Rect(center, size)) ]

    def __repr__(self):
        child_str = "None"
        if self.children:
            child_str = ", ".join(str(c) for c in self.children)
        return "%s->%d {%s}" % (str(self.rect), len(self.data) if self.data else 0, child_str)
            

#end PointTree


# Tree encompassing a normal RectTree to allow for it to be dynamically expanded to
# any size based on the data inserted into it.
class ExpandingRectTree:

    def __init__(self, init_rect):
        self.root = RectTree(init_rect)

    # override the default insert to check for data
    # falling outside of the current tree.
    def insert(self, data):

        # expand tree until it can contain new data
        while not self.root.rect.contains(data.getPosition()):
            self._expandTree(data)

        return self.root.insert(data)

    def _expandTree(self, data):
        
        # double the size of the tree
        newSize = self.root.rect.size * 2

        # instead of having complex logic to determine how to expand
        # this rect, we just create all rects and use _childIndex to choose one.
        pos = self.root.rect.getPosition()
        size = self.root.rect.size
        rects = ( Rect(pos - size, newSize),
                  Rect(pos - Point(0, size.y), newSize),
                  Rect(pos - Point(size.x, 0), newSize),
                  Rect(pos, newSize) )
        idx = self._childIndex(data)
        newRoot = RectTree(rects[idx])
        newRoot.children = newRoot._createChildren()

        # replace a child of the new root with the old one
        newRoot.children[newRoot._childIndex(self.root.rect)] = self.root
        self.root = newRoot

    def __getattr__(self, name):
        # pass all remaining attribute calls to the root
        return getattr(self.root, name)
#end ExpandingRectTree
