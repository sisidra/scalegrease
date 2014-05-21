import logging
import subprocess
from scalegrease.system import check_output
from scalegrease.runner import RunnerBase


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
