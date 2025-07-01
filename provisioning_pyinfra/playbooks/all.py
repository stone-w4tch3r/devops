from tasks.root_password import deploy_root_password
from tasks.server_upgrade import server_upgrade
from tasks.server_user import deploy_server_user
from tasks.shell_aliases import deploy_aliases
from tasks.ssh_hardening import deploy_ssh_hardening
from tasks.ssh_keys import deploy_ssh_keys
from tasks.ufw import deploy_ufw
from tasks.disable_ipv6_ufw import disable_ipv6_ufw
from tasks.zsh import deploy_zsh
from tasks.disable_ipv6 import disable_ipv6
from tasks.shell_tools import deploy_shell_tools

server_upgrade()
deploy_server_user()
deploy_shell_tools()
deploy_zsh()
deploy_aliases()
deploy_ssh_keys()
deploy_ufw()
deploy_ssh_hardening()
deploy_root_password()
disable_ipv6()
disable_ipv6_ufw()
