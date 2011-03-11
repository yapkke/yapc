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
    @return (status, output)
    """
    out = []
    cref = os.popen(cmd, 'r')
    for l in cref:
        out.append(l)
    ret = cref.close()
    if (ret == None):
        ret = 0

    output.dbg(cmd+" (returns "+str(ret)+")", classname)
    return (ret, out)

def run_cmd_screen(name, cmd, classname):
    """Run command in screen
    
    @param name name of screen
    @param cmd command
    @param classname name of class calling command
    """
    return run_cmd("screen -dm -S "+name+" -e ^Oo "+cmd, classname)
