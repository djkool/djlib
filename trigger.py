#!/usr/bin/env python
"""
trigger.py : Basic Trigger/Events system.

TriggerManager - Tracks triggers and updates them as needed.
Trigger - Base Trigger class
Timer - Timer Trigger to perform actions after a set amount of time.
"""

###############################################################################
##  TriggerManager

class TriggerManager(object):
	
	def __init__(self, gc):
		self.gc = gc
		self.triggers = []


	def update(self, dt):
		# Erase triggers as they trigger
		self.triggers = [x for x in self.triggers if not (x.update(dt) and x.autoremove)]


	def addTrigger(self, trigger, autoremove = True):
		self.triggers.append(trigger)
		trigger.tmgr = self
		return trigger


	def removeTrigger(self, trigger):
		self.triggers.remove(trigger)


	def addTimer(self, delay, callback, recurring = False):
		return self.addTrigger(Timer(delay, callback, recurring))

#end TriggerManager


###############################################################################
##  Trigger

class Trigger(object):
	
	def __init__(self, callback = None, autoremove = True):
		self.tmgr = None
		self.callback = callback
		self.autoremove = autoremove

		self.running = False
		self.triggered = False


	def update(self, dt):
		return False

	def reset(self):
		self.running = False
		self.triggered = False

	def _run(self):
		self.running = True
		if self.callback:
			self.callback(self)

		self.triggered = True
		self.running = False

	def __repr__(self):
		return "Trigger running=%s triggered=%s" % (str(self.running), str(self.triggered))

#end Trigger


###############################################################################
##  Timer

class Timer(Trigger):

	def __init__(self, delay, callback, recurring = False):
		Trigger.__init__(self, callback, not recurring)
		self.delay = delay
		self.recurring = recurring

		self.reset()


	def update(self, dt):
		# Reset recurring triggers before doing anything else
		if self.triggered:
			self.reset()
			if not self.recurring:
				return True

		# Run based on time
		self.time += dt
		if self.time >= self.delay:
			self._run()
		return False


	def reset(self):
		Trigger.reset(self)
		self.time = 0.0

#end Timer

###############################################################################
##  ProximityTrigger

class ProximityTrigger(Trigger):
	from .primitives import BoundingVolume

	def __init__(self, entity, bound_vol, callback = None):
		Trigger.__init__(self, callback, False)
		self.entity = entity
		if not isinstance(bound_vol, ProximityTrigger.BoundingVolume): raise TypeError()
		self.bound_vol = bound_vol

	def update(self, dt):
		if self.bound_vol.contains(self.entity):
			if not self.triggered:
				self._run()
		elif self.triggered:
			# Reset on leave
			self.reset()
		return False

#end ProximityTrigger