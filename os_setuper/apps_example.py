import app
from app import App, Apt, AptPpa, Snap, Dnf
from common import OS

current_os = OS.ubuntu


def main():
    apps = [
        App(
            ({
                OS.ubuntu: Apt(Name="firefox", RepoOrPpa=AptPpa("ppa:mozillateam/ppa")),
                OS.fedora: Dnf(Name="firefox")
            })[current_os]
        ),
        App(Name="VLC", Installation=Apt(Name="vlc")),
        App(Snap("multipass"), "multipass"),  # todo not installs
        App("neofetch"),
    ]

    app.handle(apps)


main()  # todo properly handle if __name__ == "__main__"
