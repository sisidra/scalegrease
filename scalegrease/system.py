import subprocess


class CalledProcessError(subprocess.CalledProcessError):
    """
    Python 2.6 subprocess.CalledProcessError has no "output" property.
    """
    def __init__(self, returncode, cmd, output=None):
        super(CalledProcessError, self).__init__(returncode, cmd)
        self.output = output

    def __str__(self):
        return super(CalledProcessError, self).__str__() + ('\nOutput:\n"""\n%s"""' % self.output)


def check_output(cmd, env=None):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
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
