from dataclasses import dataclass


@dataclass
class Rule:
    RuleText: str
    RegexToReplace: str


ssh_hardening_rules = [
    Rule("PasswordAuthentication no", r"^PasswordAuthentication"),
    Rule("PermitRootLogin no", r"^PermitRootLogin"),
    Rule("PermitEmptyPasswords no", r"^PermitEmptyPasswords"),
    Rule("X11Forwarding no", r"^X11Forwarding"),
]
