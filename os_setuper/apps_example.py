import structured_config
from common import OS

current_os = OS.ubuntu


def main():
    # apps = [
    #     App(
    #         ({
    #             OS.ubuntu: Apt(PackageName="firefox", RepoOrPpa=AptPpa("ppa:mozillateam/ppa")),
    #             OS.fedora: Dnf(PackageName="firefox")
    #         })[current_os]
    #     ),
    #     App(Installation=Apt(PackageName="vlc")),
    #     App(Snap("multipass")),
    #     App("neofetch"),
    # ]
    # 
    # app.handle(apps)
    structured_config.modify_config(
        entries=[
            structured_config.EntryState(Property="key", Value="value", Present=True, Overwrite=True),
        ],
        config_type=structured_config.ConfigType.json,
        path="/var/lib/cloud/data/status.json",
    )


main()  # todo properly handle if __name__ == "__main__"
