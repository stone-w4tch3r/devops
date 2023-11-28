from dataclasses import dataclass


@dataclass
class Rule:
    RuleText: str
    RegexToReplace: str


ssh_hardening_rules = [
    Rule("PasswordAuthentication yes", r"^PasswordAuthentication"),
    Rule("PermitRootLogin yes", r"^PermitRootLogin"),
    Rule("PermitEmptyPasswords no", r"^PermitEmptyPasswords"),
    Rule("X11Forwarding no", r"^X11Forwarding"),
]
