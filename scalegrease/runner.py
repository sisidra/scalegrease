import abc
import argparse
import logging
import sys

from scalegrease import deploy
from scalegrease import error
from scalegrease import system


class RunnerBase(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        self._config = config

    @abc.abstractmethod
    def run_job(self, artifact_storage, argv):
        raise NotImplementedError()


class ShellRunner(RunnerBase):
    def run_job(self, artifact_storage, argv):
        cmd_line = argv + [artifact_storage.jar_path(), artifact_storage.spec()]
        logging.info(' '.join(cmd_line))
        output = system.check_output(cmd_line)
        logging.info(output)


def find_runner(runner_name, config):
    names = config['runners']
    for rn in names:
        if rn.split('.')[-1].lower() in (runner_name.lower(), runner_name.lower() + "runner"):
            clazz = system.load_class(rn)
            class_config = config.get(clazz.__name__)
            return clazz(class_config)


def run(runner_name, artifact_spec, runner_argv, config):
    runner = find_runner(runner_name, config)
    if runner is None:
        raise error.Error("Failed to find runner '%s'" % runner_name)
    artifact_storage = deploy.ArtifactStorage.resolve(artifact_spec)
    job_argv = artifact_storage.fetch(runner_argv)
    try:
        runner.run_job(artifact_storage, job_argv)
    except system.CalledProcessError as e:
        logging.exception("Runner %s failed" % runner_name)
        raise


def extra_arguments(parser):
    parser.add_argument("--runner", "-r", required=True,
                        help="Specify runner to use, e.g. hadoop, luigi.  "
                             "It should match one of the runner names in the config, "
                             "optionally with 'runner' removed.")
    parser.add_argument(
        "artifact",
        help="Specify Maven artifact to download and run, either on format "
             "group_id:artifact_id:version or group_id:artifact_id for latest version.")


def main(argv):
    args, conf, rest_argv = system.initialise(argv, extra_arguments)
    try:
        run(args.runner, args.artifact, rest_argv, conf)
    except error.Error:
        logging.exception("Job failed")
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
