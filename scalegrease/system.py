import subprocess


def check_output(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = process.communicate()
    exit_code = process.poll()
    if exit_code:
        raise subprocess.CalledProcessError(exit_code, cmd, output=output)
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
