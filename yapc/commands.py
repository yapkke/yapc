##YAPC command running
#
# Running commands in subshell
#
# @author ykk
# @date Feb 2011
#
import os

def run_cmd(self, cmd, classname=None):
    """Run command
    
    @param cmd command
    @param classname name of class calling command
    """
    ret = os.system(cmd)
    if (classname == None):
        classname = self.__class__.__name__
    output.dbg(cmd+" returns ("+str(ret)+")", classname)
    return ret

def run_cmd_screen(self, name, cmd, classname):
    """Run command in screen
    
    @param name name of screen
    @param cmd command
    @param classname name of class calling command
    """
    return self.__run_cmd("screen -dm -S "+name+" -e ^Oo "+cmd, classname)
