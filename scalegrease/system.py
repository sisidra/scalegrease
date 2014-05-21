import subprocess


def check_output(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = process.communicate()
    exit_code = process.poll()
    if exit_code:
        raise subprocess.CalledProcessError(exit_code, cmd, output=output)
    return output


def write_file(content, settings):
    f = open(settings, "w")
    f.write(content)
    f.close()
