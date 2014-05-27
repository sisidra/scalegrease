import os
import shutil
import subprocess
import tempfile
import zipfile
import argparse

from scalegrease import system
from scalegrease.runner import RunnerBase


class LuigiRunner(RunnerBase):
    def __init__(self, config):
        super(LuigiRunner, self).__init__(config)
        self.tmp_dir = None

    def is_recognised(self, jar_path, argv):
        """
        Check by searching for luigi required parameters (module and task).
        """
        parser = argparse.ArgumentParser()
        parser.add_argument("--module", "-m")
        parser.add_argument("--task")
        args, _ = parser.parse_known_args(argv)
        return args.module and args.task

    def run_job(self, jar_path, artifact_spec, argv):
        self.tmp_dir = tempfile.mkdtemp()
        try:
            self._extract_luigi_resources(jar_path)
            self._run_luigi_task(artifact_spec, argv)
        finally:
            shutil.rmtree(self.tmp_dir)

    def _extract_luigi_resources(self, jar_path):
        jar_file = zipfile.ZipFile(jar_path, "r")
        for info in jar_file.infolist():
            resource_path = info.filename

            if resource_path.startswith("python/"):
                jar_file.extract(info, self.tmp_dir)

    def _run_luigi_task(self, artifact_spec, cmd_args):
        runner_cmd = self._config["command"]

        sub_env = os.environ.copy()
        sub_env["PLATFORM_ARTIFACT_SPEC"] = artifact_spec

        src_path = os.path.join(self.tmp_dir, "python")
        if sub_env["PYTHONPATH"]:
            sub_env["PYTHONPATH"] += ":" + src_path
        else:
            sub_env["PYTHONPATH"] = src_path

        cmd_line = [runner_cmd] + list(cmd_args)

        process = subprocess.Popen(
            cmd_line,
            env=sub_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        output, _ = process.communicate()
        exit_code = process.poll()
        print output
        if exit_code:
            raise system.CalledProcessError(exit_code, cmd_line, output=output)
