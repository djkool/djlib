#!/usr/bin/env python
"""
utils.py : Various utilities needed for games.

"""

from abc import ABCMeta


"""
enum - Emulate the enumeration functionality of other languages

Example:
ConnState = enum("DISCONNECTED",
                 "CONNECTING",
                 "CONNECTED",
                 "AUTHENTICATING",
                 "AUTHENTICATED")

state = Connstate.DISCONNECTED
"""
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    enums["debug"] = sequential
    return type('Enum', (), enums)
#end enum


"""
flags - Define a set of bit separated flags.

Example:
Format = flags(
        "NONE",
        "CENTER_HORZ",
        "CENTER_VERT",
        "CENTER_FULL",
        "PAD_HORZ",
        "PAD_VERT",
        "PAD_FULL",
    )

format = Format.CENTER_HORZ | Format.PAD_VERT
"""
def flags(*sequential, **named):
    flags = dict(zip(sequential, [0]+[1 << x for x in range(len(sequential)-1)]), **named)
    flags["debug"] = sequential
    return type('Flags', (), flags)
#end flags


"""
Singletone - Parent class to create single instance global objects.
"""
class Singleton:

    _instance = None

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls.__new__(cls)
            cls._instance.init()
        return cls._instance

    def init(self):
        """ Replaces __init__ for the Singletone class"""
        pass

    def __init__(self):
        raise NotImplementedError("%s is a singleton. Use `instance()` to access." % self.__class__.__name__)

#end Singleton


"""
Interface - Base class to define interfaces where issubclass/isinstance will fail if subclasses have
not implemented all the methods of the interface. Ignores "_****" methods.
"""
class Interface(metaclass=ABCMeta):

    @classmethod
    def _findInterface(cls, subclass):
        mro = type.mro(subclass)
        for c in mro[1:]:
            if c is Interface:
                return subclass
            subclass = c

    @classmethod
    def __subclasshook__(cls, subclass):
        interface = cls._findInterface(subclass)
        if not interface:
            return False

        for attr in interface.__dict__:
            if not attr.startswith('_'):
                attrfunc = getattr(subclass, attr, None)
                if not attrfunc or not callable(attrfunc) or attrfunc is interface.__dict__[attr]:
                    return False
        return True

#end Interface


class IAllocator(Interface):
    def allocate(self, reserve):
        """Allocates a unique object, or reserves space for an existing one."""

    def deallocate(self, value):
        """Deallocates a previously allocated or reserved object for reuse."""
#end IAllocator


class IdAllocator(IAllocator):

    def __init__(self, start_id = 0, end_id = None):
        if end_id:
            assert start_id < end_id
        self.start = start_id
        self.end = end_id
        self.curr = start_id

    def allocate(self, reserve = None):
        if self.empty():
            return None #Generator is empty
            
        if reserve and self.curr < reserve:
            self.curr = reserve + 1
        else:
            reserve = self.curr
            self.curr = self.curr + 1

        return reserve

    def deallocate(self, value):
        #deallocate does nothing for a basic allocator
        pass

    def empty(self):
        return self.end and self.curr >= self.end

#end IdAllocator
IAllocator.register(IdAllocator)
