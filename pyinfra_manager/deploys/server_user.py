from pyinfra import host
from pyinfra.operations import server


def deploy_server_user() -> None:
    server_user = host.data.server_user
    server_user_password = host.data.server_user_password

    server.group(group="docker", _sudo=True)

    server.user(
        user=server_user,
        home=f"/home/{server_user}",
        groups=["sudo", "docker"],
        shell="/bin/bash",
        _sudo=True
    )

    server.shell(
        name="Shell: Ensure password",
        commands=f"echo '{server_user}:{server_user_password}' | sudo chpasswd",
        _sudo=True
    )
