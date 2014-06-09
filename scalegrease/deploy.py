import logging
import os
from xml.etree import ElementTree

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
        mvn_get_cmd = [
            "mvn", "-e", "-o" if offline else "-U",
            "org.apache.maven.plugins:maven-dependency-plugin:2.8:get",
            "-Dartifact=%s:%s:%s:jar:jar-with-dependencies" %
            (artifact.group_id, artifact.artifact_id, artifact.version)]

        logging.info(" ".join(mvn_get_cmd))
        mvn_get_out = system.check_output(mvn_get_cmd)
        logging.debug(mvn_get_out)
        # The maven dependency plugin does not report which version is the latest, so peek into the
        # local repository.  There are other plugins, e.g. versions-maven-plugin that can, but they
        # require a pom, so that's a bit messy as well.
        local_repo = "%s/.m2/repository" % os.environ["HOME"]
        version = determine_latest(local_repo, artifact)
        versioned_artifact = artifact.with_version(version)
        jar_path = "%s/%s" % (local_repo, versioned_artifact.jar_path())
        logging.info("Downloaded %s to %s", artifact.spec(), jar_path)
        return jar_path

    except system.CalledProcessError as e:
        logging.error("Maven failed: %s, output:\n%s", e, e.output)
        raise error.Error("Download failed: %s\n%s" % (e, e.output))


def determine_latest(repo, artifact):
    error_msg = "Failed to find latest version metadata for " + artifact.spec()
    metadata = "%s/%s/maven-metadata-repo.xml" % (repo, artifact.path())
    try:
        tree = ElementTree.parse(metadata)
    except IOError as err:
        raise error.Error("%s: %s" % (error_msg, err))
    latest = tree.findall(".versioning/latest")
    if len(latest) != 1:
        raise error.Error("%s: Unexpected XML content", error_msg)
    return latest[0].text


class Artifact(object):
    def __init__(self, group_id, artifact_id, version="LATEST"):
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.version = version

    def path(self):
        return "%s/%s" % (self.group_id.replace(".", "/"), self.artifact_id)

    def spec(self):
        return ':'.join((self.group_id, self.artifact_id, self.version))

    def jar_name(self):
        return "%s-%s-jar-with-dependencies.jar" % (self.artifact_id, self.version)

    def jar_path(self):
        return "%s/%s/%s" % (self.path(), self.version, self.jar_name())

    def with_version(self, version):
        return Artifact(self.group_id, self.artifact_id, version)

    @classmethod
    def parse(cls, artifact_spec):
        return Artifact(*artifact_spec.split(':'))
