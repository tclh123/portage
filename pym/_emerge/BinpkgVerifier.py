from _emerge.AsynchronousTask import AsynchronousTask
from portage.util import writemsg
import sys
# for an explanation on this logic, see pym/_emerge/__init__.py
import os
import sys
if os.environ.__contains__("PORTAGE_PYTHONPATH"):
	sys.path.insert(0, os.environ["PORTAGE_PYTHONPATH"])
else:
	sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "pym"))
import portage
class BinpkgVerifier(AsynchronousTask):
	__slots__ = ("logfile", "pkg",)

	def _start(self):
		"""
		Note: Unlike a normal AsynchronousTask.start() method,
		this one does all work is synchronously. The returncode
		attribute will be set before it returns.
		"""

		pkg = self.pkg
		root_config = pkg.root_config
		bintree = root_config.trees["bintree"]
		rval = os.EX_OK
		stdout_orig = sys.stdout
		stderr_orig = sys.stderr
		log_file = None
		if self.background and self.logfile is not None:
			log_file = open(self.logfile, 'a')
		try:
			if log_file is not None:
				sys.stdout = log_file
				sys.stderr = log_file
			try:
				bintree.digestCheck(pkg)
			except portage.exception.FileNotFound:
				writemsg("!!! Fetching Binary failed " + \
					"for '%s'\n" % pkg.cpv, noiselevel=-1)
				rval = 1
			except portage.exception.DigestException, e:
				writemsg("\n!!! Digest verification failed:\n",
					noiselevel=-1)
				writemsg("!!! %s\n" % e.value[0],
					noiselevel=-1)
				writemsg("!!! Reason: %s\n" % e.value[1],
					noiselevel=-1)
				writemsg("!!! Got: %s\n" % e.value[2],
					noiselevel=-1)
				writemsg("!!! Expected: %s\n" % e.value[3],
					noiselevel=-1)
				rval = 1
			if rval != os.EX_OK:
				pkg_path = bintree.getname(pkg.cpv)
				head, tail = os.path.split(pkg_path)
				temp_filename = portage._checksum_failure_temp_file(head, tail)
				writemsg("File renamed to '%s'\n" % (temp_filename,),
					noiselevel=-1)
		finally:
			sys.stdout = stdout_orig
			sys.stderr = stderr_orig
			if log_file is not None:
				log_file.close()

		self.returncode = rval
		self.wait()

