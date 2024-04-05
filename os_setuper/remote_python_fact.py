from dataclasses import dataclass

from pyinfra import host
from pyinfra.api import FactBase


@dataclass
class InterpreterInfo:
    Version: str
    InterpreterCommand: str


@dataclass(frozen=True)
class RemotePythonInfo:
    Python2Interpreters: list[InterpreterInfo]
    Python3Interpreters: list[InterpreterInfo]


class _RemotePython2Result(FactBase):
    command = "python2 --version"

    def process(self, output) -> InterpreterInfo | None:
        if not output:
            return None
        return InterpreterInfo(Version=output[0].strip(), InterpreterCommand="python2")


class _RemotePython3Result(FactBase):
    command = "python3 --version"

    def process(self, output) -> InterpreterInfo | None:
        if not output:
            return None
        return InterpreterInfo(Version=output[0].strip(), InterpreterCommand="python3")


class _RemoteBasePythonResult(FactBase):
    command = "python --version"

    def process(self, output) -> InterpreterInfo | None:
        if not output:
            return None
        return InterpreterInfo(Version=output[0].strip(), InterpreterCommand="python")


class RemotePython(FactBase):
    """
    Returns information about Python interpreters available on the remote host.

    @return: RemotePythonInfo
    """
    command = "echo nothing"

    def process(self, output) -> RemotePythonInfo:
        python: InterpreterInfo = host.get_fact(_RemoteBasePythonResult)
        python2: InterpreterInfo = host.get_fact(_RemotePython2Result)
        python3: InterpreterInfo = host.get_fact(_RemotePython3Result)

        pythons2 = [p for p in [python, python2, python3] if p and p.Version.startswith("Python 2")]
        pythons3 = [p for p in [python, python2, python3] if p and p.Version.startswith("Python 3")]

        return RemotePythonInfo(Python2Interpreters=pythons2, Python3Interpreters=pythons3)
