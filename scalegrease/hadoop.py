import logging
import subprocess

from scalegrease import system
from scalegrease import runner


class HadoopRunner(runner.RunnerBase):
    def is_recognised(self, jar_path, argv):
        """
        Check by searching jar content for .class file from specified class name (first argument).
        """

        if len(argv) == 0:
            return False

        try:
            jar_listing = system.check_output(["jar", "tf", jar_path])
            class_path = argv[0].replace(".", "/") + ".class"
            return class_path in jar_listing.splitlines()
        except system.CalledProcessError:
            return False

    def run_job(self, jar_path, artifact_spec, argv):
        hadoop_cmd = self._config["command"] + [jar_path]
        logging.info("Executing: %s", " ".join(hadoop_cmd))
        subprocess.check_call(hadoop_cmd)
