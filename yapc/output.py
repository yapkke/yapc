##This module implements output printing.
#
# Output are divided into 4 levels and
# can be configured for different verbosity
#
# (copied from pylibopenflow on Oct 2010)
#
# @author ykk
# @date Aug 2009
#
import logging

##Level of messages
global LEVELS 
LEVELS = {"ERR": 40,
          "WARN": 30,
          "INFO": 20,
          "DBG": 10,
          "VDBG": 1}

##Dictionary of loggers
loggers = {}

#Global mode
global output_mode
output_mode = None

#Indicate if log to console
global toconsole
toconsole = True

#Stream handler
global console
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(asctime)s - %(name)s - "\
                                           "%(levelname)s -  %(message)s"))

def __create_logger(who, level):
    """Create logger for who

    @param who module name for logging
    @param level level to log
    """
    global loggers
    global toconsole
    global LEVELS
    loggers[who] = logging.getLogger(who)
    loggers[who].setLevel(level)
    if (toconsole):
        loggers[who].addHandler(console)
    loggers["generic"].log(LEVELS["VDBG"],
                           "Add logger for "+who+" at level "+str(level))

def set_mode(msg_mode, who=None):
    """Set the message mode for who
    If who is None, set global mode
    """
    global output_mode
    global LEVELS
    global loggers

    #Global mode
    if (output_mode == None):
        output_mode = "WARN"
    if (who == None):
        output_mode = msg_mode
        __create_logger("generic", LEVELS[output_mode])

    #Individual mode
    if (who != None and who not in loggers):
        __create_logger(who, LEVELS[msg_mode])
    
def output(msg_mode, msg, who=None):
    """Print message
    """
    global output_mode
    global LEVELS
    global loggers
    if (output_mode == None):
        raise RuntimeException("Output mode is not set")

    #Indicate who string
    if (who == None):
        who = "generic"
    
    #Ensure logger exists
    if (who not in loggers):
        __create_logger(who, LEVELS[output_mode])
        
    #Log message
    loggers[who].log(LEVELS[msg_mode], msg)
         
def err(msg, who=None):
    """Print error messages
    """
    output("ERR", msg, who)

def warn(msg, who=None):
    """Print warning messages
    """
    output("WARN", msg, who)

def info(msg, who=None):
    """Print informational messages
    """
    output("INFO", msg, who)

def dbg(msg, who=None):
    """Print debug messages
    """
    output("DBG", msg, who)

def vdbg(msg, who=None):
    """Print verbose debug messages
    """
    output("VDBG", msg, who)
