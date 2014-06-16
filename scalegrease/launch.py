import logging
import re
import os
import glob

from scalegrease import error
from scalegrease import system


def maven_output(mvn_cmd):
    lines = system.check_output(mvn_cmd).splitlines()
    return '\n'.join(filter(lambda li: not re.match(r"^\[(INFO|DEBUG)\]", li), lines))


def launch(crontab_glob, pom_file, conf):
    all_crontabs = glob.glob(crontab_glob)
    if not all_crontabs:
        logging.warn("No crontab files found matching '%s', pwd=%s", crontab_glob, os.getcwd())
    group_id = maven_output(
        ["mvn", "-f", pom_file, "help:evaluate", "-Dexpression=project.groupId"]).strip()
    logging.info("Determined groupId: %s" % group_id)
    artifact_id = maven_output(
        ["mvn", "-f", pom_file, "help:evaluate", "-Dexpression=project.artifactId"]).strip()
    logging.info("Determined artifactId: %s" % artifact_id)

    launch_conf = conf['launch']
    repo_host = launch_conf['crontab_repository_host']
    repo_dir = launch_conf['crontab_repository_dir']

    clean_cmd = ["ssh", repo_host, "rm", "-f", "%s/%s__%s__*" % (repo_dir, group_id, artifact_id)]
    logging.info("Removing old crontabs: %s", ' '.join(clean_cmd))
    clean_output = system.check_output(clean_cmd)
    logging.info("Ssh output: %s", clean_output)

    for crontab in all_crontabs:
        dst_name = "__".join([group_id, artifact_id, os.path.basename(crontab)])
        scp_cmd = ["scp", crontab, "%s:%s/%s" % (repo_host, repo_dir, dst_name)]
        logging.info(' '.join(scp_cmd))
        scp_output = system.check_output(scp_cmd)
        logging.info("Scp output: %s" % scp_output)


def add_arguments(parser):
    parser.add_argument("--cron-glob", "-g", default="src/main/cron/*.cron",
                        help="Glob pattern for enumerating cron files")
    parser.add_argument("--pom-file", "-p", default="pom.xml",
                        help="Path to project pom file")


def main(argv):
    args, conf, _ = system.initialise(argv, add_arguments)

    try:
        launch(args.cron_glob, args.pom_file, conf)
    except error.Error:
        logging.exception("Job failed")
        return 1
