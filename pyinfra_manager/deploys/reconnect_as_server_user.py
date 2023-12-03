import os
from time import sleep

from pyinfra import host
from pyinfra.connectors.util import remove_any_sudo_askpass_file
from pyinfra.facts import files
from pyinfra.operations import python, server


def _update_connection_data(server_user: str, server_user_password: str, ssh_key_path: str) -> None:
    host.data.override_datas["ssh_user"] = server_user
    host.data.override_datas["ssh_password"] = server_user_password
    host.data.override_datas["_use_sudo_password"] = server_user_password

    if os.path.isfile(ssh_key_path):
        host.data.override_datas["ssh_key"] = ssh_key_path


def _wait_and_reconnect(state, host) -> None:
    delay = 2
    max_retries = 5

    host.connection = None
    retries = 0

    while True:
        host.connect(show_errors=False)
        if host.connection:
            break

        if retries > max_retries:
            raise Exception(f"Connection failed after {retries} retries")

        sleep(delay)
        retries += 1


def _fix_sudo() -> None:
    remove_any_sudo_askpass_file(host)


def reconnect_as_server_user() -> None:
    server_user = host.data.server_user
    server_user_password = host.data.server_user_password
    ssh_key_path = host.data.ssh_key_path

    python.call(
        name="Update connection data",
        function=lambda: _update_connection_data(server_user, server_user_password, ssh_key_path)
    )
