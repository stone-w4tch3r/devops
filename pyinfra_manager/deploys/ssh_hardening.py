from pyinfra import host
from pyinfra.api.operation import OperationMeta
from pyinfra.operations import files, server

from deploys.ssh_hardening_vars import ssh_hardening_rules


def deploy_ssh_hardening():
    configs = ["/etc/ssh/sshd_config", *host.get_fact(files.FindFiles, "/etc/ssh/sshd_config.d")]

    results = []
    for config in configs:
        for rule in ssh_hardening_rules:
            res = files.line(path=config, replace=rule.RuleText, line=rule.RegexToReplace, _sudo=True)
            results.append(res)

    were_changes = True in [result.changed for result in results]
    if were_changes:
        server.service(service="sshd", restarted=True, _sudo=True)
