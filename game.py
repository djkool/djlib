#!/usr/bin/env python
"""
game.py : Provides a basic framework for game looping and states.

"""
__author__ = "Andrew Peterson (DJKool14)"
__copyright__ = "Copyright 2021, DJLib Project [https://github.org/djkool/djlib]"
__credits__ = []


class GameClass:
    
    def __init__(self):
        self.curr_state = None
        self.running = False
        self.known_states = {}

    def initialize(self):
        self.running = True

    def update(self):
        if self.curr_state:
            self.curr_state.processInput()
            self.curr_state.update()

            self.curr_state.render()

    def changeState(self, state_class, *args):
        assert(state_class)

        if self.curr_state:
            # Don't switch to the same state
            if state_class is self.curr_state.__class__:
                return

            # Leave the current state
            self.curr_state.leave()

        # look for state class in known states
        new_state = self.known_states.get(state_class)
        if not new_state:
            # Instantiate class
            new_state = state_class()
            self.known_states[state_class] = new_state

            # initialize new state
            new_state.gc = self
            new_state.initialize()

        # officially switch to new state
        self.curr_state = new_state

        # Finally enter into the next state
        self.curr_state.enter(*args)

    def closeState(self, state_class):

        # Look for state in known states
        if state in self.known_states:
            # shutdown and remove from list
            state.shutdown()
            self.known_states.remove(state)
            return True
        return False

    def shutdown(self):
        self.running = False

        # Leave the current state we are in
        if self.curr_state:
            self.curr_state.leave()
            self.curr_state = None

        # Shutdown all known states
        for state in self.known_states.values():
            state.shutdown()
        self.known_states = {}

    def getActiveState(self):
        return self.curr_state
        
#end GameClass

class GameState:

    def __init__(self):
        self.gc = None

    def initialize(self):
        """Called the first time the game is changed to this state
           during the applications lifecycle."""

    def enter(self):
        """Called every time the game is switched to this state."""

    def processInput(self):
        """Called during normal update/render period for this state
           to process it's input."""

    def update(self):
        """Called during normal update/render period for this state
           to update it's local or game data."""

    def render(self):
        """Called during normal update/render period for this state
           to render it's data in a specific way."""

    def leave(self):
        """Called whenever we switch from this state to another."""

    def shutdown(self):
        """Called during application shutdown."""

    def changeState(self, state_class, *args):
        """Shortcut for this state to initiate transfer to a new state."""
        self.gc.changeState(state_class, *args)

#end GameState

