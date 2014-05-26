import logging
import re
import subprocess

from scalegrease import error
from scalegrease import system


def mvn_download(artifact, tmp_dir, offline):
    """Download artifact from maven repository to local directory.

    Maven will by default do local repository caching for us, which we want in order to avoid
    hammering the artifactory server, and also to avoid the artifactory being a single point of
    failure.  An artifactory failure will prevent new versions from getting rolled out, but not
    jobs from running.
    """
    try:
        # Notes on maven behaviour:  In case of network failure, it will reuse the locally cached
        # repository metadata gracefully, and therefore use the latest downloaded version.
        # In case multiple maven processes are running, they might download a new artifact
        # concurrently.  Maven downloads to temporary file and renames, however, so each file
        # download is atomic, and no external locking should be needed.
        mvn_copy_cmd = [
            "mvn", "-e", "-o" if offline else "-U", "org.apache.maven.plugins:maven-dependency-plugin:2.8:copy",
            "-DoutputDirectory=" + tmp_dir,
            "-Dartifact=%s:%s:%s:jar:jar-with-dependencies" % (artifact.group_id(), artifact.artifact_id(), artifact.version())]

        logging.info(" ".join(mvn_copy_cmd))
        mvn_copy_out = system.check_output(mvn_copy_cmd)
        copying_re = r'Copying .*\.jar to (.*)'
        match = re.search(copying_re, mvn_copy_out)
        jar_path = match.group(1)
        logging.info("Downloaded %s:%s to %s", artifact.spec, artifact.version(), jar_path)
        logging.debug(mvn_copy_out)
        return jar_path

    except subprocess.CalledProcessError as e:
        logging.error("Maven failed: %s, output:\n%s", e, e.output)
        raise error.Error("Download failed: %s\n%s" % (e, e.output))


class Artifact(object):
    def __init__(self, spec):
        self.spec = spec

    def path(self):
        return "%s/%s" % (self.group_id().replace(".", "/"), self.artifact_id())

    def _parts(self):
        return self.spec.split(":")

    def artifact_id(self):
        return self._parts()[1]

    def group_id(self):
        return self._parts()[0]

    def version(self):
        if len(self._parts()) < 3:
            return "LATEST"
        return self._parts()[2]
