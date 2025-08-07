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

# Create
distrobox create \
  --name "${CONTAINER_NAME:-dev}" \
  --image "${BASE_IMAGE:-fedora-toolbox:42}" \
  --init \
  --unshare-all \
  --additional-packages "git openssh-server micro" \
  --additional-flags "--publish ${SSH_PORT:-2222}:22" \
  --additional-flags "--env \"SSH_KEY_NAME=${SSH_KEY_NAME:-distrobox-key}\"" \
  --volume ~/.ssh/${SSH_KEY_NAME:-distrobox-key}.pub:/tmp/host-ssh-key/${SSH_KEY_NAME:-distrobox-key}.pub:ro \
  --volume ~/Projects/devops/provisioning_distrobox/distrobox-init.sh:/tmp/container-init.sh:ro \
  --init-hooks "/tmp/container-init.sh" \
  --volume ~/.claude/:${HOME}/.claude/:rw \
  --volume ~/.claude.json:${HOME}/.claude.json:rw \
  --volume ~/.claude.json.backup:${HOME}/.claude.json.backup:rw \
  --volume ~/Projects/kotatogram-fork/:${HOME}/kotatogram-fork:rw \
  --yes

# Start SSH service
distrobox enter "${CONTAINER_NAME:-dev}" -- echo configured!

# Enter
ssh -p "${SSH_PORT:-2222}" ${USER}@localhost -o StrictHostKeyChecking=no -i ~/.ssh/distrobox-key
```
