# not runnable
return 1

read -r -s password && echo "$password" \
  | ansible -i hosts.yml -e "ansible_password=$password ansible_become_pass=$password" \
  -m ping primary