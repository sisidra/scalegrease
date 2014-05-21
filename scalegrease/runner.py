import abc
import argparse
import logging
import shutil
import sys
import tempfile

from scalegrease import deploy
from scalegrease import error
from scalegrease import system


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


def find_runner(jar_path):
    # TODO: Read runner list from config file
    names = ["scalegrease.runner.ShellRunner", "scalegrease.hadoop.HadoopRunner",
             "scalegrease.luigi.LuigiRunner"]
    runners = []
    for rn in names:
        clazz = system.load_class(rn)
        runners.append(clazz())
    for r in runners:
        if r.is_recognised(jar_path):
            return r


def run(artifact_spec, version):
    artifact = deploy.Artifact(artifact_spec)
    tmp_dir = tempfile.mkdtemp(prefix="greaseworker")
    jar_path = deploy.download(artifact, tmp_dir, version)
    worker = find_runner(jar_path)
    if worker is None:
        raise error.Error("Failed to find a worker for %s" % artifact_spec)
    worker.run_job(jar_path)
    shutil.rmtree(tmp_dir)


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


if __name__ == '__main__':
    sys.exit(main(sys.argv))
