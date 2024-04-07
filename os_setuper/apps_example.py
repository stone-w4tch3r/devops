import app
from app import App, Apt, Dnf, Snap, AptPpa
from common import OS
from lib import structured_config

current_os = OS.ubuntu


def main():
    apps = [
        App(
            ({
                OS.ubuntu: Apt(PackageName="firefox", RepoOrPpa=AptPpa("ppa:mozillateam/ppa")),
                OS.fedora: Dnf(PackageName="firefox")
            })[current_os]
        ),
        App(Installation=Apt(PackageName="vlc")),
        App(Snap("multipass")),
        App("neofetch"),
    ]

    # app.handle(apps)

    structured_config.modify_config(
        modify_action=lambda config: config,
        config_type=structured_config.ConfigType.JSON,
        path="/run/cloud-init/instance-data.json",
        backup=False,
    )


main()  # todo properly handle if __name__ == "__main__"
