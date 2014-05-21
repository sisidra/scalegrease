import abc


class RunnerBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def is_recognised(self, jar_path):
        raise NotImplementedError()

    @abc.abstractmethod
    def run_job(self, jar_path):
        raise NotImplementedError()


class ShellRunner(RunnerBase):
    def is_recognised(self, jar_path):
        pass

    def run_job(self, jar_path):
        pass
