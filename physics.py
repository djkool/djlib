#!/usr/bin/env python
"""
physics.py : Very basic physical entity helpers.

"""
__author__ = "Andrew Peterson (DJKool14)"
__copyright__ = "Copyright 2017, DJLib Project [https://github.org/djkool/djlib]"
__credits__ = []


# IMPORTS
from .primitives import Entity
from .primitives import Vector

# CONSTANTS
DEFAULT_MAX_VEL = 10.0
DEFAULT_MASS = 10.0
DEFAULT_RADIUS = 10.0

def inRange(value, lower, upper):
    return lower <= value <= upper

class Attributes:
    def __init__(self, max_vel=DEFAULT_MAX_VEL, mass=DEFAULT_MASS,
                        radius=DEFAULT_RADIUS):
        self.max_vel = max_vel
        self.mass = mass
        self.radius = radius
        
#end PhysicalAttributes


class PhysicsEntity(Entity):
    def __init__(self, position, phys_attributes):
        Entity.__init__(self, position)
        self.phys_attrs = phys_attributes
        self.vel = Vector(0,0)

    def update(self, time_step):
        # Enforce velocity cap
        if self.vel.length() > self.phys_attrs.max_vel:
            self.vel = self.vel.normalized() * self.phys_attrs.max_vel
            
        # update position using velocity
        self.pos = self.pos + (self.vel*time_step)

    def setPosition(self, pos):
        Entity.setPosition(self, pos)

        # clear physics data on position move
        self.vel.clear()
        self.accel = None
        
    def setVelocity(self, vel):
        # cap velocity to the max velocity defined in our physical attributes
        if vel.length() > self.phys_attrs.max_vel:
            vel = vel.normalized() * self.phys_attrs.max_vel
        self.vel = vel

    def isMoving(self):
        return self.vel.length() > 0
    
    def size(self):
        return self.phys_attrs.radius

    def __getattr__(self, attr):
        return getattr(self.phys_attrs, attr)
        
