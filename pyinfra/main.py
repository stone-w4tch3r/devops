from pyinfra.operations import apt

apt.packages(
    name="Ensure iftop is installed",
    packages=["iftop"],
    update=True,
    _sudo=True,
)

print('hello')
