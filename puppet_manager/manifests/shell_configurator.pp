
class puppet_manager::shell_configurator {
  package { ['zsh', 'git', 'curl']:
    ensure => installed,
  }
}
