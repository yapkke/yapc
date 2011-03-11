##YAPC command running
#
# Running commands in subshell
#
# @author ykk
# @date Feb 2011
#
import os
import yapc.output as output

SCREEN = "screen"

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
    return run_cmd(SCREEN+" -dm -S "+name+" -e ^Oo "+cmd, classname)

def kill_screen(name, classname):
    """Kill screen
    
    @param name name of screen
    @param classname name of class calling command
    """
    return run_cmd(SCREEN+" -d -r "+name+" -X quit", classname)

def __parse_screen_list(line):
    """Line of screen list
    """
    result = {}
    s = line.split()
    result["fullname"] = s[0]
    ss = s[0].split(".")
    result["pid"] = ss[0]
    result["name"] = ss[1]
    result["date"] = s[1][1:]
    result["time"] = s[2]+" "+s[3]
    result["status"] = s[4][1:-1]
    return result

def list_screen(classname):
    """List screen

    @param classname name of class calling command
    """
    (ret, out) = run_cmd(SCREEN+" -ls", classname)
    if (len(out) == 2):
        return None
    else:
        screenlist = []
        for s in out[1:-2]:
            screenlist.append(__parse_screen_list(s))
        return screenlist

