from pyinfra import host
from pyinfra.operations import files, server

from deploys.ssh_hardening_vars import ssh_hardening_rules


def deploy_ssh_hardening():
    configs = ["/etc/ssh/sshd_config", *host.get_fact(files.FindFiles, "/etc/ssh/sshd_config.d")]

    for config in configs:
        for rule in ssh_hardening_rules:
            files.line(path=config, replace=rule.RegexToReplace, line=rule.RuleText, _sudo=True)

    server.service(service="sshd", restarted=True, _sudo=True)
