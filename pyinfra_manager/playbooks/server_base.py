from pyinfra import host

from deploys.disable_ipv6 import disable_ipv6
from deploys.root_password import deploy_root_password
from deploys.server_upgrade import server_upgrade
from deploys.server_user import deploy_server_user
from deploys.shell_aliases import deploy_aliases
from deploys.ssh_hardening import deploy_ssh_hardening
from deploys.ssh_keys import deploy_ssh_keys
from deploys.ufw import deploy_ufw

if not host.data.aliases_complexity:
    host.data.aliases_complexity = "Minimal"

server_upgrade()
deploy_server_user()
deploy_ssh_hardening()
deploy_ssh_keys()
deploy_aliases()
deploy_ufw()
deploy_root_password()
disable_ipv6()
