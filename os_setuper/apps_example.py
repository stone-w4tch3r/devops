import app
from app import App, Apt, Brew, AptPpa
from common import OS

current_os = OS.ubuntu

apps = [
    App(
        Name="Firefox",
        Source=({
            OS.ubuntu: Apt(Name="firefox", RepoOrPpa=AptPpa("ppa:mozillateam/ppa")),
            OS.osx: Brew(Name="firefox")
        })[current_os]
    ),
    App(
        Name="VLC",
        Source=({
            OS.ubuntu: Apt(Name="vlc"),
            OS.osx: Brew(Name="vlc")
        })[current_os]
    ),
]

app.handle(apps)
