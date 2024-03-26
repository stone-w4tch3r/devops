import inspect
from typing import Callable

from pyinfra.api import operation, OperationValueError
from pyinfra.operations import files


@operation
def execute_on_remote(func: Callable, func_args: list[str] = None, func_kwargs: dict[str, str] = None):
    if func_args is None:
        func_args = []
    if func_kwargs is None:
        func_kwargs = {}

    file_path = "/tmp/remote_python.py"

    try:
        inspect.getsource(func)
    except Exception as e:
        raise OperationValueError(f"Failed to get source code of passed function: [{func}]\n\n{e}")
    if not inspect.isfunction(func):
        raise OperationValueError("Provided object is not a function.")
    if inspect.isbuiltin(func):
        raise OperationValueError("Cannot serialize built-in functions.")
    if inspect.ismethod(func):
        raise OperationValueError("Cannot serialize methods. Please provide a function.")

    source_lines = inspect.getsourcelines(func)[0]
    if source_lines[0].strip().startswith("lambda"):
        raise OperationValueError("Cannot serialize lambda functions.")

    indent_level = len(source_lines[0]) - len(source_lines[0].lstrip())
    source_without_indentation = ''.join([line[indent_level:] for line in source_lines])

    func_params_str = ", ".join(
        [f"\"{arg}\"" for arg in func_args] +
        [f"{key}=\"{value}\"" for key, value in func_kwargs.items()]
    )

    executable_code = source_without_indentation + f"\n\n{func.__name__}({func_params_str})"

    yield from files.block(
        path=file_path,
        content=executable_code,
        present=True,
    )

    yield f"python3 {file_path}"
