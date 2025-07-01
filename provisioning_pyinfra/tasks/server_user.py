from pyinfra import host
from pyinfra.operations import server, files, python


def _get_files_from_skel_and_home(home_path: str) -> (list[str], list[str]):
    files_from_skel = [file.split("/")[-1] for file in host.reload_fact(files.FindFiles, "/etc/skel")]
    files_from_home = [file.split("/")[-1] for file in host.reload_fact(files.FindFiles, home_path)]
    return files_from_skel, files_from_home


def _ensure_permissions_on_files_from_skel(home_path: str, server_user: str) -> None:
    files_from_skel, files_from_home = _get_files_from_skel_and_home(home_path)
    files_to_ensure = [file for file in files_from_home if file in files_from_skel]
    for file in files_to_ensure:
        files.file(path=f"{home_path}/{file}", user=server_user, group=server_user, mode="0644", _sudo=True)


def deploy_server_user() -> None:
    server_user = host.data.server_user
    server_user_password = host.data.server_user_password
    home_path = f"/home/{server_user}"

    server.group(group="docker", _sudo=True)

    server.user(
        user=server_user,
        home=home_path,
        groups=["sudo", "docker"],
        shell="/bin/bash",
        _sudo=True
    )

    server.shell(
        name="Shell: Ensure password",
        commands=f"echo '{server_user}:{server_user_password}' | sudo chpasswd",
        _sudo=True
    )

    files_from_skel, files_from_home = _get_files_from_skel_and_home(home_path)
    files_to_copy = [file for file in files_from_skel if file not in files_from_home]
    if any(files_to_copy):
        files_to_copy = [f"/etc/skel/{file}" for file in files_to_copy]
        server.shell(
            name="Shell: Copy files from /etc/skel to home",
            commands=f"cp -r {' '.join(files_to_copy)} {home_path}",
            _sudo=True
        )

    python.call(
        name="Ensure permissions on files from /etc/skel",
        function=lambda: _ensure_permissions_on_files_from_skel(home_path, server_user)
    )
