import logging
import os
import shutil
import tempfile
import zipfile

from scalegrease import system
from scalegrease.runner import RunnerBase


class LuigiRunner(RunnerBase):
    def run_job(self, jar_path, artifact, argv):
        tmp_dir = tempfile.mkdtemp()
        try:
            self._extract_luigi_resources(jar_path, tmp_dir)
            self._run_luigi_task(artifact, argv, tmp_dir)
        finally:
            shutil.rmtree(tmp_dir)

    def _extract_luigi_resources(self, jar_path, tmp_dir):
        jar_file = zipfile.ZipFile(jar_path, "r")
        for info in jar_file.infolist():
            resource_path = info.filename

            if resource_path.startswith("python/"):
                jar_file.extract(info, tmp_dir)

    def _run_luigi_task(self, artifact, cmd_args, tmp_dir):
        runner_cmd = self._config["command"]

        sub_env = os.environ.copy()
        sub_env["PLATFORM_ARTIFACT_SPEC"] = artifact.spec()

        src_path = os.path.join(tmp_dir, "python")
        if "PYTHONPATH" in sub_env:
            sub_env["PYTHONPATH"] += ":" + src_path
        else:
            sub_env["PYTHONPATH"] = src_path

        cmd_line = [runner_cmd] + list(cmd_args)

        output = system.check_output(cmd_line, env=sub_env)
        logging.info(output)
