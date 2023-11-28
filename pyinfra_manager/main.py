from deploys.server_upgrade import server_upgrade
from deploys.server_user import deploy_server_user
from deploys.shell_aliases import deploy_aliases
from deploys.ssh_keyed_connection import deploy_ssh_keyed_connection
from deploys.ufw import deploy_ufw
from deploys.zsh import deploy_zsh

from deploys.shell_tools import deploy_shell_tools

server_upgrade()
deploy_server_user()
deploy_zsh()
deploy_shell_tools()
deploy_aliases()
deploy_ssh_keyed_connection()
deploy_ufw()
