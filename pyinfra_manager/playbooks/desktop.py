from tasks.shell_aliases import deploy_aliases
from tasks.disable_ipv6_ufw import disable_ipv6_ufw
from tasks.zsh import deploy_zsh
from tasks.disable_ipv6 import disable_ipv6
from tasks.shell_tools import deploy_shell_tools

deploy_shell_tools()
deploy_zsh()
deploy_aliases()
disable_ipv6()
disable_ipv6_ufw()
