#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

# TODO: pass via check_and_install_all_dependencies and main
_ubuntu_version = "jammy"
_ova_file_dir = Path(__file__).parent


def _run(command: str) -> str:
    return subprocess.check_output(command, shell=True).decode().strip()


def _get_image_name() -> str:
    return f"{_ubuntu_version}-server-cloudimg-amd64.ova"


def _check_virtualbox() -> bool:
    try:
        _run("VBoxManage --version")
        return True
    except subprocess.CalledProcessError:
        return False


def _install_virtualbox() -> None:
    distro = _get_distro()
    if distro == "ubuntu" or distro == "debian":
        _run("sudo apt-get update")
        _run("sudo apt-get install -y virtualbox")
    elif distro == "fedora":
        _run("sudo dnf install -y VirtualBox")
    else:
        print(f"Unsupported distribution: {distro}")
        sys.exit(1)


def _check_cloud_image_utils() -> bool:
    try:
        _run("cloud-localds --version")
        return True
    except subprocess.CalledProcessError:
        return False


def _install_cloud_image_utils() -> None:
    distro = _get_distro()
    if distro == "ubuntu" or distro == "debian":
        _run("sudo apt-get update")
        _run("sudo apt-get install -y cloud-image-utils")
    elif distro == "fedora":
        _run("sudo dnf install -y cloud-utils-growpart")
    else:
        print(f"Unsupported distribution: {distro}")
        sys.exit(1)


def _check_ubuntu_cloud_image() -> bool:
    ova_path = Path(_ova_file_dir / _get_image_name()).expanduser()
    return ova_path.exists()


def _install_ubuntu_cloud_image() -> None:
    ova_path = Path(_ova_file_dir / _get_image_name()).expanduser()
    ova_path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        f"wget -O {ova_path} https://cloud-images.ubuntu.com/{_ubuntu_version}/current/{_ubuntu_version}-server-cloudimg-amd64.ova"
    )


def _get_distro() -> str:
    if Path("/etc/debian_version").exists():
        return "debian" if "debian" in _run("cat /etc/issue").lower() else "ubuntu"
    elif Path("/etc/fedora-release").exists():
        return "fedora"
    else:
        return "unknown"


# TODO: use in vbox_recreate.py
def check_and_install_all_dependencies(ubuntu_version: str = _ubuntu_version) -> None:
    dependencies = [
        (_check_virtualbox, _install_virtualbox, "VirtualBox"),
        (_check_cloud_image_utils, _install_cloud_image_utils, "cloud-image-utils"),
        (_check_ubuntu_cloud_image, _install_ubuntu_cloud_image, "Ubuntu cloud image"),
    ]

    for check_func, install_func, name in dependencies:
        if not check_func():
            print(f"{name} is not installed. Installing...")
            install_func()
            print(f"{name} has been installed.")
        else:
            print(f"{name} is already installed.")


# TODO: use argparse for --help support
def main() -> None:
    print("Setting up vbox_recreate script environment...")
    check_and_install_all_dependencies()
    print("Setup complete!")
    print("You can now run the VM creation script.")


if __name__ == "__main__":
    main()
