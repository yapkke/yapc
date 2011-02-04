##YAPC command running
#
# Running commands in subshell
#
# @author ykk
# @date Feb 2011
#
import os
import yapc.output as output

def run_cmd(cmd, classname):
    """Run command
    
    @param cmd command
    @param classname name of class calling command
    """
    ret = os.system(cmd)
    output.dbg(cmd+" returns ("+str(ret)+")", classname)
    return ret

def run_cmd_screen(name, cmd, classname):
    """Run command in screen
    
    @param name name of screen
    @param cmd command
    @param classname name of class calling command
    """
    return self.__run_cmd("screen -dm -S "+name+" -e ^Oo "+cmd, classname)
