import app
from app import App, Apt, AptPpa, Snap, Dnf
from common import OS

current_os = OS.ubuntu

apps = [
    App(
        ({
            OS.ubuntu: Apt(Name="firefox", RepoOrPpa=AptPpa("ppa:mozillateam/ppa")),
            OS.fedora: Dnf(Name="firefox")
        })[current_os]
    ),
    App(Name="VLC", Installation=Apt(Name="vlc")),
    App(Snap("multipass"), "multipass"),
    App("neofetch"),
]

app.handle(apps)
