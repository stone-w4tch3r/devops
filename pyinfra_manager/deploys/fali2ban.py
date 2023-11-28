from pyinfra import host
from pyinfra.facts import deb
from pyinfra.operations import apt, server, files


def deploy_fail2ban():
    if not host.get_fact(deb.DebPackage, "fail2ban"):
        apt.update(cache_time=86400, _sudo=True)
        apt.packages(packages=["fail2ban"], _sudo=True)

    server.service(service="fail2ban", running=True, enabled=True, _sudo=True)

    files.put(
        src="files/jail.local",
        dest="/etc/fail2ban/jail.local",
        mode="0644",
        _sudo=True,
    )
