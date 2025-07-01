from pyinfra import host
from pyinfra.facts import deb
from pyinfra.operations import files, server, python


def _assert_ufw_installed():
    assert host.reload_fact(deb.DebPackage, "ufw"), "ufw is not installed"


def disable_ipv6_ufw():
    python.call(
        name="Assert ufw installed",
        function=lambda: _assert_ufw_installed()
    )

    r = files.line(path="/etc/default/ufw", replace="IPV6=no", line="^IPV6=.*", _sudo=True)

    if r.changed:
        server.shell(
            name="Shell: Restart ufw",
            commands="sudo ufw reload",
            _sudo=True,
        )
