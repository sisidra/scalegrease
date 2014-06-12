import logging
import os
import re
import shutil
import tempfile

from scalegrease import error
from scalegrease import system


def extract_canonical_version(jar_path, artifact):
    jar_name = os.path.basename(jar_path)
    beginning = "{0}-".format(artifact.artifact_id)
    ending = "-{0}.{1}".format(artifact.classifier, artifact.packaging)
    if not (jar_name.startswith(beginning) and jar_name.endswith(ending)):
        raise ValueError("Jar file name does not match artifact.")
    return jar_name[len(beginning):-len(ending)]


def mvn_download(artifact, offline):
    """Download artifact from maven repository to local directory.

    Maven will by default do local repository caching for us, which we want in order to avoid
    hammering the artifactory server, and also to avoid the artifactory being a single point of
    failure.  An artifactory failure will prevent new versions from getting rolled out,
    but not prevent jobs from running.
    """
    tmp_dir = tempfile.mkdtemp(prefix="greaserun")
    try:
        # Notes on maven behaviour:  In case of network failure, it will reuse the locally cached
        # repository metadata gracefully, and therefore use the latest downloaded version.
        # In case multiple maven processes are running, they might download a new artifact
        # concurrently.  Maven downloads to temporary files and renames them, however, so each file
        # download is atomic, and no external locking should be needed.

        # We use the "copy" command rather than "get", since "get" won't tell us which version it
        # resolved to.  Discard the copied file and use the one in the local repository in order
        # to save some resources.  Consider it a way to pre-warm the OS caches. :-)
        mvn_copy_cmd = [
            "mvn", "-e", "-o" if offline else "-U",
            "org.apache.maven.plugins:maven-dependency-plugin:2.8:copy",
            "-DoutputDirectory=" + tmp_dir,
            "-Dartifact={0}".format(artifact.spec())]

        logging.info(" ".join(mvn_copy_cmd))
        mvn_copy_out = system.check_output(mvn_copy_cmd)
        logging.debug(mvn_copy_out)

        copying_re = r'Copying .*\.jar to (.*)'
        match = re.search(copying_re, mvn_copy_out)
        jar_name = match.group(1)
        version = extract_canonical_version(jar_name, artifact)
        canonical_artifact = artifact.with_canonical_version(version)

        local_repo = "%s/.m2/repository" % os.environ["HOME"]
        jar_path = "{0}/{1}".format(local_repo, canonical_artifact.jar_path())
        logging.info("Downloaded %s to %s", artifact.spec(), jar_path)
        return jar_path
    except system.CalledProcessError as e:
        logging.error("Maven failed: %s, output:\n%s", e, e.output)
        raise error.Error("Download failed: %s\n%s" % (e, e.output))
    finally:
        shutil.rmtree(tmp_dir)


class Artifact(object):
    def __init__(self, group_id, artifact_id, version="LATEST", packaging="jar",
                 classifier="jar-with-dependencies", canonical_version=None):
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.version = version
        self.packaging = packaging
        self.classifier = classifier
        self.canonical_version = canonical_version

    def path(self):
        return "%s/%s" % (self.group_id.replace(".", "/"), self.artifact_id)

    def spec(self):
        return ':'.join((self.group_id, self.artifact_id, self.version,
                         self.packaging, self.classifier))

    def jar_name(self):
        version = self.canonical_version or self.version
        return "{0}-{1}-{2}.{3}".format(
            self.artifact_id, version, self.classifier, self.packaging)

    def jar_path(self):
        return "%s/%s/%s" % (self.path(), self.version, self.jar_name())

    def with_canonical_version(self, canonical_version):
        return Artifact(
            self.group_id,
            self.artifact_id,
            version=self.version,
            canonical_version=canonical_version
        )

    @classmethod
    def parse(cls, artifact_spec):
        """Parse a maven artifact specifier.

        Note that the weird part ordering documented in http://maven.apache.org/pom.html does not
        match the implementation in maven..."""
        return Artifact(*artifact_spec.split(':'))
