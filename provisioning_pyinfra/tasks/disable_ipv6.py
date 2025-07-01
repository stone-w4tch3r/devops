from pyinfra.operations import server, files


def disable_ipv6():
    files.file(path="/etc/sysctl.d/98-disable-ipv6.conf", _sudo=True)
    r = files.block(
        path="/etc/sysctl.d/98-disable-ipv6.conf",
        marker="#### {mark} DISABLE IPV6 BLOCK ####",
        content=[
            "net.ipv6.conf.all.disable_ipv6 = 1",
            "net.ipv6.conf.default.disable_ipv6 = 1",
            "net.ipv6.conf.lo.disable_ipv6 = 1",
        ],
        present=True,
        _sudo=True,
    )

    if r.changed:
        server.shell(
            name="Shell: Reload sysctl",
            commands="sudo sysctl -p",
            _sudo=True
        )
