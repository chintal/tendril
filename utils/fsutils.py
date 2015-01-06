"""
Filesystem Utils Module Documentation (:mod:`utils.fsutils`)
============================================================
"""

import tempfile
import atexit
import os
import glob
import string


if tempfile.tempdir is None:
    tempfile.tempdir = tempfile.mkdtemp()

TEMPDIR = tempfile.gettempdir()


class VersionedOutputFile:
    """This is like a file object opened for output, but it makes
    versioned backups of anything it might otherwise overwrite.

    http://code.activestate.com/recipes/52277-saving-backups-when-writing-files/
    """

    def __init__(self, pathname, numsavedversions=3):
        """Create a new output file.

        `pathname' is the name of the file to [over]write.
        `numSavedVersions' tells how many of the most recent versions
        of `pathname' to save."""

        self._pathname = pathname
        self._tmpPathname = "%s.~new~" % self._pathname
        self._numSavedVersions = numsavedversions
        self._outf = open(self._tmpPathname, "wb")

    def __del__(self):
        self.close()

    def close(self):
        if self._outf:
            self._outf.close()
            self._replace_current_file()
            self._outf = None

    def as_file(self):
        """Return self's shadowed file object, since marshal is
        pretty insistent on working w. pure file objects."""
        return self._outf

    def __getattr__(self, attr):
        """Delegate most operations to self's open file object."""
        return getattr(self.__dict__['_outf'], attr)

    def _replace_current_file(self):
        """Replace the current contents of self's named file."""
        self._backup_current_file()
        os.rename(self._tmpPathname, self._pathname)

    def _backup_current_file(self):
        """Save a numbered backup of self's named file."""
        # If the file doesn't already exist, there's nothing to do.
        if os.path.isfile(self._pathname):
            new_name = self._versioned_name(self._current_revision() + 1)
            os.rename(self._pathname, new_name)

            # Maybe get rid of old versions.
            if (self._numSavedVersions is not None) and (self._numSavedVersions > 0):
                self._delete_old_revisions()

    def _versioned_name(self, revision):
        """Get self's pathname with a revision number appended."""
        return "%s.~%s~" % (self._pathname, revision)

    def _current_revision(self):
        """Get the revision number of self's largest existing backup."""
        revisions = [0] + self._revisions()
        return max(revisions)

    def _revisions(self):
        """Get the revision numbers of all of self's backups."""

        revisions = []
        backup_names = glob.glob("%s.~[0-9]*~" % self._pathname)
        for name in backup_names:
            try:
                revision = int(string.split(name, "~")[-2])
                revisions.append(revision)
            except ValueError:
                # Some ~[0-9]*~ extensions may not be wholly numeric.
                pass
        revisions.sort()
        return revisions

    def _delete_old_revisions(self):
        """Delete old versions of self's file, so that at most
        self._numSavedVersions versions are retained."""

        revisions = self._revisions()
        revisions_to_delete = revisions[:-self._numSavedVersions]
        for revision in revisions_to_delete:
            pathname = self._versioned_name(revision)
            if os.path.isfile(pathname):
                os.remove(pathname)


def fsutils_cleanup():
    try:
        os.rmdir(tempfile.gettempdir())
    except OSError:
        pass

atexit.register(fsutils_cleanup)
