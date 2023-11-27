class puppet_manager::docker_installer(
) {
  class { 'docker':
    docker_users => ['ubuntu'],
    noop         => $_noop,
  }

}
