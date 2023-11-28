from pyinfra.operations import server, apt


def deploy_ufw():
    apt.update(cache_time=86400, _sudo=True)
    apt.packages(packages=["ufw"], _sudo=True)

    server.shell(
        name="Shell: enable ufw, deny incoming, allow outgoing, allow ssh, reload",
        commands=[
            "sudo ufw --force enable",
            "sudo ufw default deny incoming",
            "sudo ufw default allow outgoing",
            "sudo ufw allow ssh",
            "sudo ufw reload"
        ],
        _sudo=True
    )
