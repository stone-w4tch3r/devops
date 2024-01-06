from pyinfra import host
from pyinfra.operations import files, server

from tasks.ssh_hardening_vars import ssh_hardening_rules, ssh_non_root_hardening_rules


def deploy_ssh_hardening():
    results = []
    server_user = host.data.server_user

    for rule in ssh_hardening_rules:
        res = files.line(path="/etc/ssh/sshd_config", replace=rule.RuleText, line=rule.RegexToReplace, _sudo=True)
        results.append(res)

    if server_user != "root":
        for rule in ssh_non_root_hardening_rules:
            res = files.line(path="/etc/ssh/sshd_config", replace=rule.RuleText, line=rule.RegexToReplace, _sudo=True)
            results.append(res)

    for config in [*host.get_fact(files.FindFiles, "/etc/ssh/sshd_config.d")]:
        for rule in ssh_hardening_rules:
            res = files.replace(
                path=config,
                text=rule.RegexToReplace,
                replace=f"# COMMENTED BY PYINFRA: {rule.RegexToReplace[1:]}",
                _sudo=True
            )
            results.append(res)

    were_changes = True in [result.changed for result in results]
    if were_changes:
        server.service(service="sshd", restarted=True, _sudo=True)
