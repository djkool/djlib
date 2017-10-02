#!/usr/bin/env python
"""
logger.py : Logging enhancement framework.

"""
__author__ = "Andrew Peterson (DJKool14)"
__copyright__ = "Copyright 2017, DJLib Project [https://github.org/djkool/djlib]"
__credits__ = []


from logging import *

stack_depth = 0

# XXX TODO: Should this only be done during some kind of logging initialization?
CALL = 5 # below DEBUG(10)
addLevelName(CALL, "CALL")

def add_log_args(arg_parser):
	# TODO: Add argements for stream location and trace filters
	arg_parser.add_argument('-v', '--verbose', action='count', default=0,
                     		help='Change the verbosity of the logging, each "-v" increases the ammount of logging '
                           		 'by default this program will log at level INFO ("-vvv"). '
                        		 '(levels: ERROR, WARN, INFO, DEBUG)')

def set_log_options(parsed_args, root_name):
    root_log = getLogger(root_name)

    log_lvl = min(5, parsed_args.verbose)
    root_log.setLevel({0: INFO, #default
                       1: ERROR,
                       2: WARN,
                       3: INFO,
                       4: DEBUG,
                       5: CALL
                      }.get(log_lvl, 0))

    # Until log stream options are added, we will just use the default stream
    handler = StreamHandler()

    # change formatter depending on log level.
    # debugging needs more info than general output
    format_str = '%(levelname)-6s %(message)s'
    if log_lvl > 3:
    	format_str = '%(asctime)10s.%(msecs)3d %(levelname)-6s %(name)-24s %(message)s'
    	
    handler.setFormatter(Formatter(format_str, '%c'))
    root_log.addHandler(handler)

def log_function(logger, level = CALL):
	def wrap_func(func):
		def logged(*args, **kwargs):
			global stack_depth
			logger.log(level, "%s[ENTRY] %s::%s%s", stack_depth*'  ', func.__module__, func.__name__, str(args))
			stack_depth += 1
			ret = func(*args, **kwargs)
			stack_depth -= 1
			logger.log(level, "%s[EXIT ] %s::%s(...) -> (%s)", stack_depth*'  ', func.__module__, func.__name__, str(ret))
			return ret
		return logged
	return wrap_func

def log_method(logger, level = CALL):
	def wrap_method(method):
		def logged(self, *args, **kwargs):
			global stack_depth
			logger.log(level, "%s[ENTRY] %s[%X].%s%s", stack_depth*'  ', self.__class__.__name__, id(self), method.__name__, str(args))
			stack_depth += 1
			ret = method(self, *args, **kwargs)
			stack_depth -= 1
			logger.log(level, "%s[EXIT ] %s[%X].%s(...)->{%s}", stack_depth*'  ', self.__class__.__name__, id(self), method.__name__, str(ret))
			return ret
		return logged
	return wrap_method
