from pyinfra.operations import apt, files, server
from pyinfra import host

# apt.packages(
#     name="Ensure nano is installed",
#     packages=["nano"],
#     update=True,
#     _sudo=True,
# )
# 
# server.user(
#     name="Create lord user",
#     user="lord",
#     home="/home/lord",
#     _sudo=True,
# )
# 
# files.file(
#     name="Create lord log file",
#     path="/var/log/lord.log",
#     user="lord",
#     group="lord",
#     mode="644",
#     _sudo=True,
# )

print(host.data.test_setting)
