from pyinfra import host
from pyinfra.operations import server


def deploy_root_password():
    server.shell(
        name="Shell: change root password",
        commands=f"echo 'root:{host.data.root_password}' | sudo chpasswd",
        _sudo=True
    )
