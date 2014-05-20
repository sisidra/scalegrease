import abc
import json
import logging
import shutil
import urllib
import urllib2
import argparse
import sys
import tempfile
import subprocess


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Increase debug verbosity")
    parser.add_argument(
        "artifact",
        help="Specify Maven artifact to download and run, e.g. com.spotify.data:super-cruncher")
    parser.add_argument("--version", "-V", help="Artifact version to download")
    args = parser.parse_args(argv[1:])

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    try:
        run(args.artifact, args.version)
    except Error as e:
        logging.error("Job failed: %s", e)
        return 1


class Error(Exception):
    pass


class Artifact(object):
    def __init__(self, spec):
        self.spec = spec

    def path(self):
        return "%s/%s" % (self.group_id().replace(".", "/"), self.artifact_id())

    def artifact_id(self):
        return self.spec.split(":")[-1]

    def group_id(self):
        return self.spec.split(":")[0]


class RunnerBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def is_recognised(self, jar_path):
        raise NotImplementedError()

    @abc.abstractmethod
    def run_job(self, jar_path):
        raise NotImplementedError()


class ShellRunner(RunnerBase):
    def is_recognised(self, jar_path):
        pass

    def run_job(self, jar_path):
        pass


def check_output(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = process.communicate()
    exit_code = process.poll()
    if exit_code:
        raise subprocess.CalledProcessError(exit_code, cmd, output=output)
    return output


class HadoopRunner(RunnerBase):
    def is_recognised(self, jar_path):
        try:
            jar_listing = check_output(["jar", "tf", jar_path])
            return "org/apache/crunch/Pipeline.class" in jar_listing.splitlines()
        except subprocess.CalledProcessError:
            return False

    def run_job(self, jar_path):
        hadoop_cmd = ["hadoop", "jar", jar_path]
        logging.info("Executing: %s", " ".join(hadoop_cmd))
        subprocess.check_call(hadoop_cmd)


class LuigiRunner(RunnerBase):
    def run_job(self, jar_path):
        pass

    def is_recognised(self, jar_path):
        pass


def find_worker(jar_path):
    for worker in ShellRunner(), HadoopRunner(), LuigiRunner():
        if worker.is_recognised(jar_path):
            return worker


def run(artifact_spec, version):
    artifact = Artifact(artifact_spec)
    tmp_dir = tempfile.mkdtemp(prefix="spworker")
    jar_path = download(artifact, tmp_dir, version)
    worker = find_worker(jar_path)
    if worker is None:
        raise Error("Failed to find a worker for %s" % artifact_spec)
    worker.run_job(jar_path)
    shutil.rmtree(tmp_dir)


def write_file(content, settings):
    f = open(settings, "w")
    f.write(content)
    f.close()


def fetch_repo_info(url):
    logging.debug("Retrieving %s", url)
    rsp = urllib2.urlopen(url)
    contents = rsp.read()
    repo_info = json.loads(contents)
    return repo_info


def download(artifact, tmp_dir, version):
    # TODO: Don't use artifactory REST, use maven instead.
    repo_url = "https://artifactory.spotify.net/artifactory/api/storage/libs-release-local"
    artifact_url = "%s/%s" % (repo_url, artifact.path())
    repo_info = fetch_repo_info(artifact_url)
    versions = [ch["uri"][1:] for ch in repo_info["children"]]
    latest_version = sorted(versions, key=lambda v: map(int, v.split('.')))[-1]

    jar_base = ("%s-%s-jar-with-dependencies.jar" % (artifact.artifact_id(), latest_version))
    jar_info_url = ("%s/%s/%s" % (artifact_url, latest_version, jar_base))
    jar_info = fetch_repo_info(jar_info_url)
    jar_url = jar_info["downloadUri"]
    jar_local = "%s/%s" % (tmp_dir, jar_base)
    urllib.urlretrieve(jar_url, filename=jar_local)
    return jar_local


if __name__ == '__main__':
    sys.exit(main(sys.argv))
