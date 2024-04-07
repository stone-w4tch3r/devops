from app import App, Apt, Dnf, Snap, AptPpa
from common import OS
from lib import modify_file

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

    modify_file.modify_structured_config(
        path="/file1.json",
        modify_action=lambda cfg: cfg["cars"]["car9"].set("Mercedes"),
    )

    modify_file.modify_structured_config(
        path="/file2.json",
        modify_action=lambda lst: lst.append("Mercedes"),
    )

    modify_file.modify_structured_config(
        path="/file3.json",
        modify_action=lambda dct: dct.modify_chained(
            [
                lambda x: x.set({"friends": ["Alice", "Bob"]}),
                lambda x: x["age"].set(25),
                lambda x: x["names"].set(["Alice", "Bob"]),
                lambda x: x["names"].append("Charlie"),
            ]
        )
    )


main()
