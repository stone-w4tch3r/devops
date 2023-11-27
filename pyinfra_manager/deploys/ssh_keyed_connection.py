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


def generate_and_install_ssh_key_locally(ssh_key: str, local_known_hosts: str) -> None:
    run_locally(f"ssh-keygen -f {local_known_hosts} -R primary.multipass", ignore_errs=True)
    run_locally(f"ssh-keyscan -H {host.name} >> {local_known_hosts}")

    if os.path.isfile(ssh_key):
        os.remove(ssh_key)
        os.remove(ssh_key + ".pub")
    # -q: quiet, -N: passphrase, -f: filename
    run_locally(f"ssh-keygen -t rsa -f {ssh_key} -q -N ''", ignore_errs=True)
    run_locally(f"chmod 600 {ssh_key}")


def deploy_ssh_keyed_connection() -> None:
    local_known_hosts = f"/home/{os.getlogin()}/.ssh/known_hosts"
    overwrite = host.data.get("overwrite_ssh") is True
    ssh_key = host.data.ssh_key_path
    server_user = host.data.server_user
    server_user_password = host.data.server_user_password

    python.call(lambda: assert_user_exists(server_user))

    if overwrite or open(local_known_hosts).read().find(host.name) == -1 or not os.path.isfile(ssh_key):
        python.call(lambda: generate_and_install_ssh_key_locally(ssh_key, local_known_hosts))

    python.call(
        lambda: server.user_authorized_keys(user=server_user, public_keys=[ssh_key + ".pub"], _sudo=True)
    )

    for config in ["/etc/ssh/sshd_config", *host.get_fact(files.FindFiles, "/etc/ssh/sshd_config.d")]:
        files.line(path=config, replace="PasswordAuthentication no", line="PasswordAuthentication yes", _sudo=True)
        files.line(path=config, replace="PermitRootLogin no", line="PermitRootLogin yes", _sudo=True)

    server.service(service="sshd", restarted=True, _sudo=True)

    python.call(lambda: update_connection_data(ssh_key, server_user, server_user_password))
