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

    def set_dict(d: dict) -> dict:
        d["friends"].append({"name": "Alice", "age": 30})
        return d

    structured_config.modify_config(
        path="/file.json",
        modify_action=lambda config: set_dict(config),
    )


main()  # todo properly handle if __name__ == "__main__"
