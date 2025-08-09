Launch a dev container example:

```bash
distrobox create \
  --name kotatogram-dev \
  --image registry.fedoraproject.org/fedora-toolbox:42 \
  --additional-packages "flatpak flatpak-builder git" \
  --init-hooks "sudo flatpak remote-add --if-not-exists --system flathub https://flathub.org/repo/flathub.flatpakrepo && sudo flatpak install -y org.freedesktop.Sdk/x86_64/24.08" \
  --unshare-all \
  --volume ~/Projects/org.telegram.desktop.webview/:/var/home/user1/org.telegram.desktop.webview:rw \
  --volume ~/Projects/kotatogram-fork/:/var/home/user1/kotatogram-fork:rw
```

Configurable distrobox setup:

```bash
# Configuration variables
SSH_PORT=2222
CONTAINER_NAME="dev"
SSH_KEY_NAME="distrobox-key"
BASE_IMAGE="fedora-toolbox:42"
PROJECT="project"

# Create
distrobox create \
  --name "${CONTAINER_NAME:-dev}" \
  --image "${BASE_IMAGE:-fedora-toolbox:42}" \
  --init \
  --unshare-all \
  --additional-flags "--publish ${SSH_PORT:-2222}:22" \
  --additional-flags "--env \"SSH_KEY_NAME=${SSH_KEY_NAME:-distrobox-key}\"" \
  --volume ~/.ssh/${SSH_KEY_NAME:-distrobox-key}.pub:/tmp/host-ssh-key/${SSH_KEY_NAME:-distrobox-key}.pub:ro \
  --volume ~/Projects/devops/provisioning_distrobox/distrobox-init.sh:/tmp/container-init.sh:ro \
  --init-hooks "/tmp/container-init.sh" \
  --volume ~/.claude/:${HOME}/.claude/:rw \
  --volume ~/.claude.json:${HOME}/.claude.json:rw \
  --volume ~/.claude.json.backup:${HOME}/.claude.json.backup:rw \
  --volume ~/Projects/${PROJECT:project}/:${HOME}/${PROJECT:-project}:rw \
  --yes

# Start SSH service
distrobox enter "${CONTAINER_NAME:-dev}" -- echo configured!

# Enter
ssh -p "${SSH_PORT:-2222}" ${USER}@localhost -o StrictHostKeyChecking=no -i ~/.ssh/distrobox-key
```

Using distrobox assemble:

```bash
# prepare template
distrobox assemble create --name template --file ~/Projects/devops/provisioning_distrobox/distrobox.ini

# commit image
docker commit template fedora-toolbox-template:latest

# create dev container
distrobox assemble create --name default-material-dark-theme-extension-dev --replace

# pdate template
distrobox assemble create --name template --file ~/Projects/devops/provisioning_distrobox/distrobox.ini && docker commit template fedora-toolbox-template:latest && distrobox stop template --yes
```

Store ssh config:

```bash
cat ~/.ssh/config 
# Dev containers
Host task1-dev
    HostName localhost
    Port 2222
    User user1
    IdentityFile ~/.ssh/distrobox-key
    StrictHostKeyChecking no

Host windsurf-flatpak-dev
    HostName localhost
    Port 4444
    User user1
    IdentityFile ~/.ssh/distrobox-key
    StrictHostKeyChecking no
```
