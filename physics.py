#!/usr/bin/env python
"""
physics.py : Very basic physical entity helpers.

"""
__author__ = "Andrew Peterson (DJKool14)"
__copyright__ = "Copyright 2021, DJLib Project [https://github.org/djkool/djlib]"
__credits__ = []


# IMPORTS
from .primitives import Entity, Vector, Circle

# CONSTANTS
DEFAULT_MAX_VEL = 10.0
DEFAULT_MASS = 10.0
DEFAULT_DAMPEN = 0.9
DEFAULT_RADIUS = 10.0

DAMP_THRESHOLD = 2

def inRange(value, lower, upper):
    return lower <= value <= upper

class Attributes:
    def __init__(self, max_vel=DEFAULT_MAX_VEL, mass=DEFAULT_MASS,
                       dampen=DEFAULT_DAMPEN, radius=DEFAULT_RADIUS):
        self.max_vel = max_vel
        self.mass = mass
        self.dampen = dampen
        self.radius = radius

#end PhysicalAttributes


class PhysicsEntity(Entity):
    def __init__(self, position, phys_attributes):
        Entity.__init__(self, position)
        self.phys_attrs = phys_attributes
        self.vel = Vector(0,0)
        self.accel = Vector(0,0)

    def update(self, time_step):
        # Apply acceleration
        self.vel += self.accel * time_step
        #if self.accel.empty():
        #    self.dampen()

        # Enforce velocity cap
        if self.vel.length() > self.phys_attrs.max_vel:
            self.vel = self.vel.normalized() * self.phys_attrs.max_vel

        # update position using velocity
        self.pos = self.pos + (self.vel*time_step)

    def setPosition(self, pos):
        Entity.setPosition(self, pos)

        # clear physics data on position move
        self.stop()

    def setVelocity(self, vel):
        # cap velocity to the max velocity defined in our physical attributes
        if vel.length() > self.phys_attrs.max_vel:
            vel = vel.normalized() * self.phys_attrs.max_vel
        self.vel = vel
        self.accel.clear()

    def applyForce(self, force):
        accel = force * (1 / self.phys_attrs.mass)
        self.vel += accel

    def dampen(self, dx=True, dy=True):
        self.vel.set(self.vel.x * self.phys_attrs.dampen if dx else self.vel.x,
                     self.vel.y * self.phys_attrs.dampen if dy else self.vel.y)
        if self.vel.length() < DAMP_THRESHOLD:
            self.vel.clear()

    def stop(self, dx=True, dy=True):
        self.vel = Vector(0 if dx else self.vel.x, 0 if dy else self.vel.y)
        self.accel.clear()

    def isMoving(self):
        return self.vel.length() > 0

    def size(self):
        return self.phys_attrs.radius

    def getBounds(self):
        return Circle(self.pos, self.phys_attrs.radius)

    def __getattr__(self, attr):
        return getattr(self.phys_attrs, attr)

#end PhysicsEntity
