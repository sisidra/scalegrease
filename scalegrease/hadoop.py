import logging
import subprocess

from scalegrease import runner


class HadoopRunner(runner.RunnerBase):
    def run_job(self, jar_path, artifact, argv):
        hadoop_cmd = self._config["command"] + [jar_path] + argv
        logging.info("Executing: %s", " ".join(hadoop_cmd))
        subprocess.check_call(hadoop_cmd)
