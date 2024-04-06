import remote_python
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
    # structured_config.modify_config(
    #     entries=[
    #         structured_config.EntryState(Property="key", Value="value", Present=True, Overwrite=True),
    #     ],
    #     config_type=structured_config.ConfigType.json,
    #     path="/var/lib/cloud/data/status.json",
    # )

    def print_hello_world(x, y):
        print(x, y)

    remote_python.execute_function(func=print_hello_world, func_kwargs={"x": "Hello", "y": "World"})

    def create_file_if_not_exists(file_path):
        import os
        if not os.path.exists(file_path):
            open(file_path, 'w').close()

    remote_python.execute_function(func=create_file_if_not_exists, func_args=["/tmp/test.txt"])


main()  # todo properly handle if __name__ == "__main__"
