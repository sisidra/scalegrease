import os
import shutil
import tempfile
import zipfile
import sys
import argparse

import luigi
import spotify.luigi.interface
from scalegrease.runner import RunnerBase


class LuigiRunner(RunnerBase):
    def __init__(self):
        self.tmp_dir = None

    def is_recognised(self, jar_path):
        pass

    def run_job(self, jar_path, *args):
        self.tmp_dir = tempfile.mkdtemp()
        sys.path.append(os.path.join(self.tmp_dir, "luigi"))
        try:
            self._extract_luigi_resources(jar_path)
            return self._run_luigi_task(jar_path, args)
        finally:
            shutil.rmtree(self.tmp_dir)

    def _extract_luigi_resources(self, jar_path):
        jar_file = zipfile.ZipFile(jar_path, "r")
        for info in jar_file.infolist():
            resource_path = info.filename

            if resource_path.startswith("luigi/"):
                jar_file.extract(info, self.tmp_dir)

    def _run_luigi_task(self, jar_path, cmd_args):
        parser = argparse.ArgumentParser()
        parser.add_argument("--module", "-m", help="Python module where task is defined")
        args, rest_cmd_args = parser.parse_known_args(cmd_args)

        rest_cmd_args.append("--jar-name")
        rest_cmd_args.append(jar_path)

        __import__(args.module)

        # until here
        worker_factory = spotify.luigi.interface.WorkerSchedulerFactory()
        luigi.run(
            cmdline_args=rest_cmd_args,
            use_optparse=True,
            worker_scheduler_factory=worker_factory
        )


if __name__ == "__main__":
    runner = LuigiRunner()
    runner.run_job(sys.argv[1], *sys.argv[2:])