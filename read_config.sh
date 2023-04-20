get_config_item(){
    local config_item=$1
    local config_value
    config_value=$(grep "$config_item" "$config_file" | cut -d '=' -f 2)
    echo "$config_value"
}

read_config(){  
    echo ">>>reading config"
    local config_file
    config_file=$(dirname "$0")/config

    _server_ip=$(get_config_item "server_ip")
    _default_user=$(get_config_item "default_user")
    _main_user=$(get_config_item "main_user")
    _default_passwd=$(get_config_item "default_passwd")
    _main_passwd=$(get_config_item "main_passwd")
    _keyname=$(get_config_item "keyname")
    _passphrase=$(get_config_item "passphrase")
    
    echo "server_ip=$_server_ip"
    echo "default_user=$_default_user"
    echo "main_user=$_main_user"
    echo "default_passwd=$_default_passwd"
    echo "main_passwd=$_main_passwd"
    echo "keyname=$_keyname"
    echo "passphrase=$_passphrase"
}

read_config