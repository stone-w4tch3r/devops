import os
import subprocess

from pyinfra.operations import server, files, python
from pyinfra import host


def run_locally(cmd: str, ignore_errs: bool = False) -> None:
    subprocess.run(cmd, shell=True, check=not ignore_errs)


def assert_user_exists(user: str) -> None:
    assert user in [user for user in host.reload_fact(server.Users)]


def update_connection_data(ssh_key: str, server_user: str, server_user_password: str) -> None:
    host.data.override_datas["ssh_key"] = ssh_key
    if host.data.ssh_user != server_user:
        host.data.override_datas["ssh_user"] = server_user
    if host.data.ssh_password != server_user_password:
        host.data.override_datas["ssh_password"] = server_user_password


def update_known_hosts_locally(local_known_hosts: str) -> None:
    run_locally(f"ssh-keygen -f {local_known_hosts} -R primary.multipass", ignore_errs=True)
    run_locally(f"ssh-keyscan {host.name} >> {local_known_hosts}")


def generate_keys(ssh_key: str) -> None:
    if os.path.isfile(ssh_key):
        os.remove(ssh_key)
        os.remove(ssh_key + ".pub")

    # -q: quiet, -N: passphrase, -f: filename
    run_locally(f"ssh-keygen -t rsa -f {ssh_key} -q -N ''", ignore_errs=True)
    run_locally(f"chmod 600 {ssh_key}")


def is_ssh_keyed_connection_deployed(local_known_hosts: str, ssh_key_path: str) -> bool:
    is_server_in_known_hosts = host.name in open(local_known_hosts).read()
    is_ssh_key_exists = os.path.isfile(ssh_key_path)
    return is_server_in_known_hosts and is_ssh_key_exists


def deploy_ssh_keyed_connection() -> None:
    ssh_key_path = host.data.ssh_key_path
    server_user = host.data.server_user
    server_user_password = host.data.server_user_password
    overwrite = host.data.get("overwrite_ssh") is True

    local_known_hosts = f"/home/{os.getlogin()}/.ssh/known_hosts"
    is_server_in_known_hosts = host.name in open(local_known_hosts).read()
    if overwrite or not is_server_in_known_hosts:
        python.call(
            name="Add server to known_hosts",
            function=lambda: update_known_hosts_locally(local_known_hosts)
        )

    is_ssh_key_existing = os.path.isfile(ssh_key_path)
    if overwrite or not is_ssh_key_existing:
        python.call(
            name="Assert user exists",
            function=lambda: assert_user_exists(server_user)
        )
        python.call(
            name="Generate keys",
            function=lambda: generate_keys(ssh_key_path)
        )
        python.call(
            name="Install public key on server",
            function=lambda: server.user_authorized_keys(user=server_user, public_keys=[ssh_key_path + ".pub"], _sudo=True)
        )
        python.call(
            name="Update connection data",
            function=lambda: update_connection_data(ssh_key_path, server_user, server_user_password)
        )
