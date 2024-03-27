import inspect
from typing import Callable

from pyinfra import host
from pyinfra.api import operation, OperationValueError, FunctionCommand
from pyinfra.facts import files as files_facts
from pyinfra.operations import files, python


@operation(is_idempotent=False)
def execute_from_function(func: Callable, func_args: list[str] = None, func_kwargs: dict[str, str] = None):
    """
    Execute a given Python function on a remote host.

    This function serializes the provided function and its arguments into a Python script as a string,
    writes to a temporary file on the remote host, and then executes using Python 3.

    @warning: Function should be defined with simple "def".
    @warning: Do not use variables from the outer scope.
    @warning: All imports should be inside the function.

    @param func: Function to be executed on the remote host.
    @param func_args: Positional arguments to pass to the function, only strings are supported.
    @param func_kwargs: Keyword arguments to pass to the function, only strings are supported.

    @raise OperationValueError: If the provided object is not a function, is a built-in function, is a method, is a lambda function, or if source code is not available.

    Example:
    ```python
    def print_hello_world(x, y):
        print(x, y)

    remote_python.execute_on_remote(func=print_hello_world, func_kwargs={"x": "Hello", "y": "World"})
    ```

    ```python
    def create_file_if_not_exists(file_path):
        import os
        if not os.path.exists(file_path):
            open(file_path, "w").close()

    remote_python.execute_on_remote(func=create_file_if_not_exists, func_args=["/tmp/test.txt"])
    ```
    """

    if func_args is None:
        func_args = []
    if func_kwargs is None:
        func_kwargs = {}

    file_name = "pyinfra_remote_python_script.py"

    try:
        inspect.getsource(func)
    except Exception as e:
        raise OperationValueError(f"Failed to get source code of passed function: [{func}]\n\n{e}")
    if not inspect.isfunction(func):
        raise OperationValueError("Provided object is not a function.")
    if inspect.isbuiltin(func):
        raise OperationValueError("Built-in functions are not supported.")
    if inspect.ismethod(func):
        raise OperationValueError("Methods are not supported.")

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

    # todo create built-in fact
    # try:
    #     _ = host.get_fact(windows_facts.Os)
    #     tmpdir_command = "echo %TEMP%"
    # except:  # noqa
    #     tmpdir_command = "echo ${TMPDIR:-/tmp}"
    tmpdir_command = "echo ${TMPDIR:-/tmp}"

    def get_tmp_and_finish():
        # todo not working
        # status, stdout, stderr = host.run_shell_command(tmpdir_command)
        status, stdout, stderr = host.run_shell_command("exit 1")
        assert status is True, f"Failed to get temporary directory: {stderr}"
        tmpdir: str = stdout[0]

        script_path = f"{tmpdir}/{file_name}"

        yield from files.block(
            path=script_path,
            content=executable_code,
            try_prevent_shell_expansion=True,
            present=True,
        )

        def assert_script_file_created():
            assert host.reload_fact(files_facts.File, "/path_not_exists"), f"Failed to create script file: {script_path}"

        # todo not working
        yield from python.call(
            name="Assert script file creation",
            function=assert_script_file_created
        )

        # todo create a fact for python and check
        yield f"python3 {script_path}"

    yield FunctionCommand(get_tmp_and_finish, (), {})
