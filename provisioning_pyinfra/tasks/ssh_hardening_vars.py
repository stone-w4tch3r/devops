from dataclasses import dataclass


@dataclass
class Rule:
    RuleText: str
    RegexToReplace: str


ssh_hardening_rules = [
    Rule("PasswordAuthentication no", r"^PasswordAuthentication"),
    Rule("PermitEmptyPasswords no", r"^PermitEmptyPasswords"),
    Rule("X11Forwarding no", r"^X11Forwarding"),
]
ssh_non_root_hardening_rules = [
    Rule("PermitRootLogin no", r"^PermitRootLogin"),
]
