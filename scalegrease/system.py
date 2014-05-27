import subprocess


class CalledProcessError(subprocess.CalledProcessError):
    """
    Python 2.6 subprocess.CalledProcessError has no "output" property.
    """
    def __init__(self, returncode, cmd, output=None):
        super(CalledProcessError, self).__init__(returncode, cmd)
        self.output = output


def check_output(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = process.communicate()
    exit_code = process.poll()
    if exit_code:
        raise CalledProcessError(exit_code, cmd, output=output)
    return output


def write_file(path, content):
    f = open(path, "w")
    f.write(content)
    f.close()


def load_class(rn):
    module_name, class_name = rn.rsplit('.', 1)
    mod = __import__(module_name, globals(), locals(), [class_name])
    clazz = getattr(mod, class_name)
    return clazz
