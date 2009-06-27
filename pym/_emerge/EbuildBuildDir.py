from _emerge.SlotObject import SlotObject
# for an explanation on this logic, see pym/_emerge/__init__.py
import os
import sys
if os.environ.__contains__("PORTAGE_PYTHONPATH"):
	sys.path.insert(0, os.environ["PORTAGE_PYTHONPATH"])
else:
	sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "pym"))
import portage
import errno
class EbuildBuildDir(SlotObject):

	__slots__ = ("dir_path", "pkg", "settings",
		"locked", "_catdir", "_lock_obj")

	def __init__(self, **kwargs):
		SlotObject.__init__(self, **kwargs)
		self.locked = False

	def lock(self):
		"""
		This raises an AlreadyLocked exception if lock() is called
		while a lock is already held. In order to avoid this, call
		unlock() or check whether the "locked" attribute is True
		or False before calling lock().
		"""
		if self._lock_obj is not None:
			raise self.AlreadyLocked((self._lock_obj,))

		dir_path = self.dir_path
		if dir_path is None:
			root_config = self.pkg.root_config
			portdb = root_config.trees["porttree"].dbapi
			ebuild_path = portdb.findname(self.pkg.cpv)
			settings = self.settings
			settings.setcpv(self.pkg)
			debug = settings.get("PORTAGE_DEBUG") == "1"
			use_cache = 1 # always true
			portage.doebuild_environment(ebuild_path, "setup", root_config.root,
				self.settings, debug, use_cache, portdb)
			dir_path = self.settings["PORTAGE_BUILDDIR"]

		catdir = os.path.dirname(dir_path)
		self._catdir = catdir

		portage.util.ensure_dirs(os.path.dirname(catdir),
			gid=portage.portage_gid,
			mode=070, mask=0)
		catdir_lock = None
		try:
			catdir_lock = portage.locks.lockdir(catdir)
			portage.util.ensure_dirs(catdir,
				gid=portage.portage_gid,
				mode=070, mask=0)
			self._lock_obj = portage.locks.lockdir(dir_path)
		finally:
			self.locked = self._lock_obj is not None
			if catdir_lock is not None:
				portage.locks.unlockdir(catdir_lock)

	def clean_log(self):
		"""Discard existing log."""
		settings = self.settings

		for x in ('.logid', 'temp/build.log'):
			try:
				os.unlink(os.path.join(settings["PORTAGE_BUILDDIR"], x))
			except OSError:
				pass

	def unlock(self):
		if self._lock_obj is None:
			return

		portage.locks.unlockdir(self._lock_obj)
		self._lock_obj = None
		self.locked = False

		catdir = self._catdir
		catdir_lock = None
		try:
			catdir_lock = portage.locks.lockdir(catdir)
		finally:
			if catdir_lock:
				try:
					os.rmdir(catdir)
				except OSError, e:
					if e.errno not in (errno.ENOENT,
						errno.ENOTEMPTY, errno.EEXIST):
						raise
					del e
				portage.locks.unlockdir(catdir_lock)

	class AlreadyLocked(portage.exception.PortageException):
		pass

