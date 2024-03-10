from pyinfra.operations import server


def main():
    server.group(group="docker", _sudo=True)

    pass
