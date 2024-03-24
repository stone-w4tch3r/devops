import app
from app import App, Apt, AptPpa, Snap, Dnf
from common import OS

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

    app.handle(apps)


main()  # todo properly handle if __name__ == "__main__"
