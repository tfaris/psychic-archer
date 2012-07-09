"""
Prints SVN logs to stdout, given a range of revisions. Doesn't matter what branch 
the revision(s) are on, the logs will be retrieved.

ex. 
python get_logs.py "/src/myWorkingDir/" "https://127.0.0.1/svn/myRepo/" 747 848 >> log747-848.txt
"""

from svn import get_logs
import sys

if __name__ == '__main__':
    args = sys.argv[1:]
    working_dir,repo,r = None,None,None
    if len(args) == 0:
        raise Exception("Working dir/repo not specified.")
    elif len(args) > 2:
        working_dir = args[0]
        repo = args[1]		
        if len(args) == 3:
            r = [args[2]]
        elif len(args) == 4:
            r = range(int(args[2]),int(args[3])+1)
    else:
        raise Exception("Not enough args")
	
    print("Getting logs for %s for revision(s) %s" % (repo, r))
        
    logs = get_logs(r,working_dir,repo)
    print logs.logs_string().encode('utf8')