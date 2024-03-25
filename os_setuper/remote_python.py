import inspect
from typing import Callable

from pyinfra.api import operation


@operation
def execute_on_remote(function: Callable, *args, **kwargs):
    file_path = "/tmp/remote_python.py"
    executable_code = inspect.getsource(function) + f"\n\n{function.__name__}(*{args}, **{kwargs})\n"

    yield f"echo '{executable_code}' > {file_path}"

    yield f"python3 {file_path}"
