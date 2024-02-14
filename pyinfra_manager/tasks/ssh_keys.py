import os
import subprocess

from pyinfra import host
from pyinfra.facts.server import Users
from pyinfra.operations import server, python


def _run_locally(cmd: str, ignore_errs: bool = False) -> None:
    subprocess.run(cmd, shell=True, check=not ignore_errs)


def _assert_user_exists(user: str) -> None:
    assert user in [user for user in host.reload_fact(server.Users)]


def _update_known_hosts_locally(local_known_hosts: str, host_name: str) -> None:
    _run_locally(f"ssh-keygen -f {local_known_hosts} -R {host_name}", ignore_errs=True)
    _run_locally(f"ssh-keyscan {host.name} >> {local_known_hosts}")


def _generate_keys(ssh_key: str) -> None:
    if os.path.isfile(ssh_key):
        os.remove(ssh_key)
        os.remove(ssh_key + ".pub")

    # -q: quiet, -N: passphrase, -f: filename, -t: type
    _run_locally(f"ssh-keygen -t rsa -f {ssh_key} -q -N ''", ignore_errs=True)
    _run_locally(f"chmod 600 {ssh_key}")


def _is_ssh_keyed_connection_deployed(local_known_hosts: str, ssh_key_path: str) -> bool:
    is_server_in_known_hosts = host.name in open(local_known_hosts).read()
    is_ssh_key_exists = os.path.isfile(ssh_key_path)
    return is_server_in_known_hosts and is_ssh_key_exists


def deploy_ssh_keys() -> None:
    ssh_key_path = host.data.ssh_key_path
    server_user = host.data.server_user
    overwrite = host.data.get("overwrite_ssh") is True

    local_known_hosts = f"/home/{os.getlogin()}/.ssh/known_hosts"
    is_server_in_known_hosts = host.name in open(local_known_hosts).read()
    if overwrite or not is_server_in_known_hosts:
        python.call(
            name="Add server to known_hosts",
            function=lambda: _update_known_hosts_locally(local_known_hosts, host.name)
        )

    is_ssh_key_existing = os.path.isfile(ssh_key_path)
    if overwrite or not is_ssh_key_existing:
        python.call(
            name="Generate keys",
            function=lambda: _generate_keys(ssh_key_path)
        )

    python.call(
        name="Assert user exists",
        function=lambda: _assert_user_exists(server_user)
    )
    python.call(
        name="Ensure public key on server",
        function=lambda: server.user_authorized_keys(
            user=server_user,
            public_keys=[ssh_key_path + ".pub"],
            authorized_key_directory=f"{host.get_fact(Users)[server_user]['home']}/.ssh",
            _sudo=True
        )
    )
