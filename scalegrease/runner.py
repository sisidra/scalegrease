import abc
import argparse
import logging
import shutil
import sys
import tempfile
import json

from scalegrease import deploy
from scalegrease import error
from scalegrease import system


class RunnerBase(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        self._config = config

    @abc.abstractmethod
    def run_job(self, jar_path, artifact, argv):
        raise NotImplementedError()


class ShellRunner(RunnerBase):
    def run_job(self, jar_path, artifact, argv):
        cmd_line = argv + [jar_path, artifact.spec()]
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


def run(runner_name, artifact_spec, mvn_offline, runner_argv, config):
    runner = find_runner(runner_name, config)
    if runner is None:
        raise error.Error("Failed to find runner '%s'" % runner_name)
    artifact_spec = deploy.Artifact.parse(artifact_spec)
    tmp_dir = tempfile.mkdtemp(prefix="greaserun")
    jar_path = deploy.mvn_download(artifact_spec, tmp_dir, mvn_offline)
    try:
        runner.run_job(jar_path, artifact_spec, runner_argv)
        shutil.rmtree(tmp_dir)
    except system.CalledProcessError as e:
        logging.error("Runner %s failed: %s" % (runner_name, e))
        raise


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file", "-c", default="/etc/scalegrease.json",
                        help="Read configuration from CONFIG_FILE")
    parser.add_argument("--runner", "-r", required=True,
                        help="Specify runner to use, e.g. hadoop, luigi.  "
                             "It should match one of the runner names in the config, "
                             "optionally with 'runner' removed.")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Increase debug verbosity")
    parser.add_argument("--mvn-offline", "-o", action="store_true",
                        help="Use Maven in offline mode")
    parser.add_argument(
        "artifact",
        help="Specify Maven artifact to download and run, either on format "
             "group_id:artifact_id:version or group_id:artifact_id for latest version.")
    args, rest_argv = parser.parse_known_args(argv[1:])
    if rest_argv[:1] == ['--']:
        # Argparse really should have removed it for us.
        rest_argv = rest_argv[1:]

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    logging.info("Reading configuration from %s", args.config_file)
    conf_file = open(args.config_file)
    conf = json.load(conf_file)
    conf_file.close()
    logging.debug("Configuration read:\n%s", conf)

    try:
        run(args.runner, args.artifact, args.mvn_offline, rest_argv, conf)
    except error.Error as e:
        logging.error("Job failed: %s", e)
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
