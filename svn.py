"""
Provides some basic scriptable usage of SVN client tools
via the eazysvn module.
"""

from lxml import etree
from Queue import Queue
from StringIO import StringIO
import os,threading,eazysvn

__author__ = "Tom Faris"

class LogEntry(object):
	"""
	A single SVN log entry.
	"""
	def __init__(self,revision,author='',date='',msg='',branch_path=''):
		self.revision = revision
		self.author = author
		self.date = date
		self.msg = msg
		self.branch_path=branch_path
		
	def __repr__(self):
		return "LogEntry(%s,%s,%s,%s,%s)" % (self.revision,self.author,self.date,self.msg,self.branch_path)

class LogCollection(list):	
	"""
	A collection of LogEntries.
	"""
	def logs_for(self,revisions=None):
		"""
		Get LogEntries for the specified revision(s).
		
		Arguments
			revisions: A string, int or list specifying the revision number(s). If None, returns this collection.
		
		Returns
			A collection of LogEntries matching the revisions specified.
		"""
		if revisions is None:
			return self
		range = []
		for entry in self:
			if isinstance(revisions,basestring) or isinstance(revisions,int):
				if entry.revision==str(revisions):
					return entry
			elif isinstance(revisions,list) and int(entry.revision) in revisions:
				range.append(entry)
		return range
		
	def logs_string(self,revisions=None):
		"""
		Creates a human-readable string of all of the log entries of the specified revisions.
		
		Arguments
			revisions: A string, int or list specifying the revision number(s). If None, returns this collection.
		"""
		logs = self.logs_for(revisions)
		s = StringIO()
		for entry in logs:
			s.write("------------------------------------------------------------------------ %s" % os.linesep)
			s.write("r%s | %s | %s" % (entry.revision,entry.author,entry.date))
			s.write(os.linesep)
			s.write(entry.msg)
			s.write(os.linesep)
		return s.getvalue()
	

def get_logs(revisions=[], working_path='', svn_path='', branch_pre='/branches/'):
	"""
	Get SVN log entries for the specified revisions, across ALL branches of the repository.
	
	Arguments:
		revisions: A list of str. The revision numbers to get log entries for.
		working_path: A local working-copy directory of the repository.
		svn_path: The end point URL of the repository. Should point to the directory that contains trunk,branches,tags,etc.
		
	Returns:
		A LogCollection containing the log entries.
	"""
	
	logs = LogCollection()
	revisions = [str(r) for r in revisions] # Make our own copy
		
	branches = eazysvn.listbranches(working_path) # Get all branches
	
	branches = ["%s%s%s" % (svn_path,branch_pre,branch) for branch in branches]
	branches.append("%s/trunk" % svn_path)
	
	# We'll thread and queue the branches separately
	thread_queue = Queue(len(branches))
	for branch in branches:
		thread = _LogGetThread(branch,revisions)
		thread.start()
		thread_queue.put(thread,True)
	
	finished = 0
	while finished < len(branches):
		thread = thread_queue.get(True)
		thread.join()		
		[logs.append(entry) for entry in thread.result]
		finished += 1
	
	# Sort the logs by revision descending
	logs.sort(key=lambda x:x.revision,reverse=True)
	return logs

class _LogGetThread(threading.Thread):	
	def __init__(self,svn_branch_path,revisions):
		self.svn_branch_path = svn_branch_path
		self.revisions = revisions
		threading.Thread.__init__(self)

	def run(self):		
		logs = []
		log_xml = eazysvn.svnlog(self.svn_branch_path)	
		tree = etree.fromstring(log_xml)		
		rev_found_here = []
		
		for i in range(0,len(self.revisions)):
			rev = self.revisions[i]
			log_entry_elements = tree.xpath("/log/logentry[@revision=%s]" % str(rev))
			for e in log_entry_elements:
				r = e.get('revision')
				if r is not None:
					rev_found_here.append(str(r))
					log = LogEntry(r,author=e.findtext('author'),date=e.findtext('date'),msg=e.findtext('msg'),branch_path=self.svn_branch_path)
					logs.append(log)
				
		self.result = logs