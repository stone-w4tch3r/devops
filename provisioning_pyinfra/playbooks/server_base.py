from pyinfra import host

from tasks.disable_ipv6 import disable_ipv6
from tasks.root_password import deploy_root_password
from tasks.server_upgrade import server_upgrade
from tasks.server_user import deploy_server_user
from tasks.ssh_hardening import deploy_ssh_hardening
from tasks.ssh_keys import deploy_ssh_keys
from tasks.ufw import deploy_ufw

# todo remove, too ugly
host.data.aliases_complexity = "Minimal"

server_upgrade()
deploy_server_user()
deploy_ssh_hardening()
deploy_ssh_keys()
deploy_ufw()
deploy_root_password()
disable_ipv6()
