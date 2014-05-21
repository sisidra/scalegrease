import logging
import shutil
import argparse
import sys
import tempfile

from scalegrease import hadoop
from scalegrease import luigi
from scalegrease import runner
from scalegrease import error
from scalegrease import deploy


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
    except error.Error as e:
        logging.error("Job failed: %s", e)
        return 1


class Artifact(object):
    def __init__(self, spec):
        self.spec = spec

    def path(self):
        return "%s/%s" % (self.group_id().replace(".", "/"), self.artifact_id())

    def artifact_id(self):
        return self.spec.split(":")[-1]

    def group_id(self):
        return self.spec.split(":")[0]


def find_runner(jar_path):
    for r in runner.ShellRunner(), hadoop.HadoopRunner(), luigi.LuigiRunner():
        if r.is_recognised(jar_path):
            return r


def run(artifact_spec, version):
    artifact = Artifact(artifact_spec)
    tmp_dir = tempfile.mkdtemp(prefix="spworker")
    jar_path = deploy.download(artifact, tmp_dir, version)
    worker = find_runner(jar_path)
    if worker is None:
        raise error.Error("Failed to find a worker for %s" % artifact_spec)
    worker.run_job(jar_path)
    shutil.rmtree(tmp_dir)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
