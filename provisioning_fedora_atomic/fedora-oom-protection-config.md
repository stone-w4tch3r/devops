# Fedora OOM Protection and System Optimization Configuration

## Overview

This document contains all the configured settings for OOM (Out of Memory) protection and system optimization on this Fedora atomic laptop. Use this as a restoration guide when reinstalling Fedora.

**System Information:**
- OS: Fedora Linux 42 (Kinoite)
- Kernel: Linux 6.15.10-200.fc42.x86_64
- CPU: 12th Gen Intel Core i5-1235U (12 threads, 10 cores, 2 threads per core)
- RAM: 24GB total
- systemd: 257.7-1.fc42

## 1. Package Installation

### Required Packages
Install these packages after fresh Fedora installation:

```bash
sudo rpm-ostree install earlyoom nvme-cli sysstat
```

### Service Enablement
Enable the following services:

```bash
sudo systemctl enable earlyoom
sudo systemctl enable sysstat
sudo systemctl enable psi-monitor.timer
sudo systemctl enable nvme-temp-monitor.timer
```

## 2. systemd Configuration

### 2.1 OOM Daemon Configuration

**File:** `/etc/systemd/oomd.conf.d/desktop-baseline.conf`
```ini
[OOM]
DefaultMemoryPressureLimit=70%
DefaultMemoryPressureDurationSec=10s
```

**Commands to apply:**
```bash
sudo mkdir -p /etc/systemd/oomd.conf.d/
sudo tee /etc/systemd/oomd.conf.d/desktop-baseline.conf << 'EOF'
[OOM]
DefaultMemoryPressureLimit=70%
DefaultMemoryPressureDurationSec=10s
EOF
```

### 2.2 Machine Slice Resource Limits

**File:** `/etc/systemd/system/machine.slice.d/limits.conf`
```ini
[Slice]
# Memory controls - throttle before swap storms and set hard limit
MemoryHigh=75%
MemoryMax=90%

# IO controls - lower priority than desktop and pressure limits
IOWeight=200
# IOPressureLimit requires systemd ≥ 258 (current: 257) - kept for future compatibility
IOPressureLimit=80% 10s

# CPU controls - on 12-thread CPU, leave 3 threads free for desktop
CPUQuota=900%
```

**Commands to apply:**
```bash
sudo mkdir -p /etc/systemd/system/machine.slice.d/
sudo tee /etc/systemd/system/machine.slice.d/limits.conf << 'EOF'
[Slice]
# Memory controls - throttle before swap storms and set hard limit
MemoryHigh=75%
MemoryMax=90%

# IO controls - lower priority than desktop and pressure limits
IOWeight=200
# IOPressureLimit requires systemd ≥ 258 (current: 257) - kept for future compatibility
IOPressureLimit=80% 10s

# CPU controls - on 12-thread CPU, leave 3 threads free for desktop
CPUQuota=900%
EOF
```

### 2.3 Graphical Slice I/O Priority

**File:** `/etc/systemd/system/graphical.slice.d/override.conf`
```ini
[Slice]
IOWeight=1000
```

**Commands to apply:**
```bash
sudo mkdir -p /etc/systemd/system/graphical.slice.d/
sudo tee /etc/systemd/system/graphical.slice.d/override.conf << 'EOF'
[Slice]
IOWeight=1000
EOF
```

## 3. Memory and Swap Configuration

### 3.1 Kernel Parameters

**File:** `/etc/sysctl.d/99-memory-tuning.conf`
```ini
# Memory and swap tuning for freeze-resistant workstation
vm.swappiness = 20

# Enable all SysRq functions for emergency recovery
kernel.sysrq = 1
```

**Commands to apply:**
```bash
sudo tee /etc/sysctl.d/99-memory-tuning.conf << 'EOF'
# Memory and swap tuning for freeze-resistant workstation
vm.swappiness = 20

# Enable all SysRq functions for emergency recovery
kernel.sysrq = 1
EOF
```

### 3.2 SysRq Configuration

**File:** `/etc/sysctl.d/99-sysrq.conf`
```ini
kernel.sysrq = 1
```

**Commands to apply:**
```bash
sudo tee /etc/sysctl.d/99-sysrq.conf << 'EOF'
kernel.sysrq = 1
EOF
```

### 3.3 Zram Configuration

**File:** `/etc/systemd/zram-generator.conf`
```ini
# This config file enables a /dev/zram0 device with smart dynamic sizing:
# — size — 75% of available RAM for optimal performance across different RAM sizes
# — compression — zstd for better performance than default lzo-rle
#
# This scales automatically: 12GB zram for 16GB RAM, 18GB zram for 24GB RAM, etc.
# To disable, uninstall zram-generator-defaults or create empty file.
[zram0]
zram-size = ram * 0.75
compression-algorithm = zstd
```

**Commands to apply:**
```bash
sudo tee /etc/systemd/zram-generator.conf << 'EOF'
# This config file enables a /dev/zram0 device with smart dynamic sizing:
# — size — 75% of available RAM for optimal performance across different RAM sizes
# — compression — zstd for better performance than default lzo-rle
#
# This scales automatically: 12GB zram for 16GB RAM, 18GB zram for 24GB RAM, etc.
# To disable, uninstall zram-generator-defaults or create empty file.
[zram0]
zram-size = ram * 0.75
compression-algorithm = zstd
EOF

# Apply the new configuration
sudo systemctl restart systemd-zram-setup@zram0.service
```

**Note:** The zram-size uses a smart dynamic formula that scales with available RAM:
- 16GB RAM system: ~12GB zram (75% of 16GB)
- 24GB RAM system: ~18GB zram (75% of 24GB) 
- 32GB RAM system: ~24GB zram (75% of 32GB)

This provides optimal swap performance while leaving enough RAM for applications. The configuration uses zstd compression for better performance than the default lzo-rle.

**Verification:**
```bash
# Check current zram configuration
swapon --show

# For 24GB RAM system, should show approximately 17-18GB zram
# NAME       TYPE       SIZE  USED PRIO
# /dev/zram0 partition 17.4G    0B   100

# Calculate expected size: (Total RAM * 0.75)
awk '/MemTotal/ {printf "Expected zram: %.1f GB\n", ($2/1024/1024)*0.75}' /proc/meminfo
```

## 4. I/O Scheduler Configuration

### 4.1 NVMe BFQ Scheduler

**File:** `/etc/udev/rules.d/60-ioschedulers.rules`
```
# Set BFQ scheduler for NVMe devices to ensure I/O fairness
ACTION=="add|change", KERNEL=="nvme[0-9]*", ATTR{queue/scheduler}="bfq"
```

**Commands to apply:**
```bash
sudo tee /etc/udev/rules.d/60-ioschedulers.rules << 'EOF'
# Set BFQ scheduler for NVMe devices to ensure I/O fairness
ACTION=="add|change", KERNEL=="nvme[0-9]*", ATTR{queue/scheduler}="bfq"
EOF

# Trigger udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

**Verification:**
```bash
# Should show [bfq] as selected scheduler
cat /sys/block/nvme0n1/queue/scheduler
```

## 5. Monitoring and Logging

### 5.1 PSI (Pressure Stall Information) Monitor

**Timer File:** `/etc/systemd/system/psi-monitor.timer`
```ini
[Unit]
Description=Run PSI monitor every minute
Requires=psi-monitor.service

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min
Persistent=true

[Install]
WantedBy=timers.target
```

**Service File:** `/etc/systemd/system/psi-monitor.service`
```ini
[Unit]
Description=PSI Monitor
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/bash -c 'echo "$(date):" >> /var/log/psi.log && echo "Memory: $(cat /proc/pressure/memory)" >> /var/log/psi.log && echo "I/O: $(cat /proc/pressure/io)" >> /var/log/psi.log && echo "CPU: $(cat /proc/pressure/cpu)" >> /var/log/psi.log && echo "---" >> /var/log/psi.log'
User=root
Group=root
```

### 5.2 NVMe Temperature Monitor

**Timer File:** `/etc/systemd/system/nvme-temp-monitor.timer`
```ini
[Unit]
Description=Run NVMe temperature monitor every 5 minutes
Requires=nvme-temp-monitor.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
```

**Service File:** `/etc/systemd/system/nvme-temp-monitor.service`
```ini
[Unit]
Description=NVMe Temperature Monitor
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/bash -c 'echo "$(date): $(nvme smart-log /dev/nvme0n1 | grep temperature)" >> /var/log/nvme-temp.log'
User=root
Group=root
```

### 5.3 Commands to Create All Monitoring Services

```bash
# Create PSI monitor timer
sudo tee /etc/systemd/system/psi-monitor.timer << 'EOF'
[Unit]
Description=Run PSI monitor every minute
Requires=psi-monitor.service

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Create PSI monitor service
sudo tee /etc/systemd/system/psi-monitor.service << 'EOF'
[Unit]
Description=PSI Monitor
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/bash -c 'echo "$(date):" >> /var/log/psi.log && echo "Memory: $(cat /proc/pressure/memory)" >> /var/log/psi.log && echo "I/O: $(cat /proc/pressure/io)" >> /var/log/psi.log && echo "CPU: $(cat /proc/pressure/cpu)" >> /var/log/psi.log && echo "---" >> /var/log/psi.log'
User=root
Group=root
EOF

# Create NVMe temperature monitor timer
sudo tee /etc/systemd/system/nvme-temp-monitor.timer << 'EOF'
[Unit]
Description=Run NVMe temperature monitor every 5 minutes
Requires=nvme-temp-monitor.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Create NVMe temperature monitor service
sudo tee /etc/systemd/system/nvme-temp-monitor.service << 'EOF'
[Unit]
Description=NVMe Temperature Monitor
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/bash -c 'echo "$(date): $(nvme smart-log /dev/nvme0n1 | grep temperature)" >> /var/log/nvme-temp.log'
User=root
Group=root
EOF

# Enable the timers
sudo systemctl enable psi-monitor.timer
sudo systemctl enable nvme-temp-monitor.timer

# Start the timers
sudo systemctl start psi-monitor.timer
sudo systemctl start nvme-temp-monitor.timer
```

## 6. EarlyOOM Configuration

EarlyOOM is enabled with default settings. The service is configured to:
- Send SIGTERM when memory available ≤ 1.69% and swap free ≤ 10.00%
- Send SIGKILL when memory available ≤ 0.84% and swap free ≤ 5.00%
- Prefer killing Web Content processes
- Avoid killing system processes like dnf, packagekitd, gnome

**Status Check:**
```bash
sudo systemctl status earlyoom
```

## 7. Emergency Access

### 7.1 SSH Service (Optional)

SSH service is currently disabled for security. Enable if remote access is needed:

```bash
sudo systemctl enable sshd
sudo systemctl start sshd
```

### 7.2 SysRq Keys

SysRq is enabled via kernel parameters. Emergency key combinations:
- `Alt + SysRq + f`: Invoke OOM killer
- `Alt + SysRq + i`: Kill all tasks except init
- `Alt + SysRq + s`: Sync all filesystems
- `Alt + SysRq + u`: Unmount all filesystems
- `Alt + SysRq + b`: Reboot immediately

## 8. Complete Restoration Script

Here's a complete script to apply all configurations after a fresh Fedora installation:

```bash
#!/bin/bash
# Fedora OOM Protection Restoration Script

set -e

echo "Installing required packages..."
sudo rpm-ostree install earlyoom nvme-cli sysstat
echo "Reboot required after package installation. Run this script again after reboot."

echo "Creating systemd configurations..."

# OOM Daemon configuration
sudo mkdir -p /etc/systemd/oomd.conf.d/
sudo tee /etc/systemd/oomd.conf.d/desktop-baseline.conf << 'EOF'
[OOM]
DefaultMemoryPressureLimit=70%
DefaultMemoryPressureDurationSec=10s
EOF

# Machine slice limits
sudo mkdir -p /etc/systemd/system/machine.slice.d/
sudo tee /etc/systemd/system/machine.slice.d/limits.conf << 'EOF'
[Slice]
# Memory controls - throttle before swap storms and set hard limit
MemoryHigh=75%
MemoryMax=90%

# IO controls - lower priority than desktop and pressure limits
IOWeight=200
# IOPressureLimit requires systemd ≥ 258 - kept for future compatibility
IOPressureLimit=80% 10s

# CPU controls - on 12-thread CPU, leave 3 threads free for desktop
CPUQuota=900%
EOF

# Graphical slice I/O priority
sudo mkdir -p /etc/systemd/system/graphical.slice.d/
sudo tee /etc/systemd/system/graphical.slice.d/override.conf << 'EOF'
[Slice]
IOWeight=1000
EOF

echo "Creating kernel parameter configurations..."

# Memory and swap tuning
sudo tee /etc/sysctl.d/99-memory-tuning.conf << 'EOF'
# Memory and swap tuning for freeze-resistant workstation
vm.swappiness = 20

# Enable all SysRq functions for emergency recovery
kernel.sysrq = 1
EOF

# SysRq configuration
sudo tee /etc/sysctl.d/99-sysrq.conf << 'EOF'
kernel.sysrq = 1
EOF

echo "Configuring zram..."

# Zram configuration
sudo tee /etc/systemd/zram-generator.conf << 'EOF'
# This config file enables a /dev/zram0 device with smart dynamic sizing:
# — size — 75% of available RAM for optimal performance across different RAM sizes
# — compression — zstd for better performance than default lzo-rle
#
# This scales automatically: 12GB zram for 16GB RAM, 18GB zram for 24GB RAM, etc.
# To disable, uninstall zram-generator-defaults or create empty file.
[zram0]
zram-size = ram * 0.75
compression-algorithm = zstd
EOF

# Apply the new zram configuration
sudo systemctl restart systemd-zram-setup@zram0.service

echo "Setting up I/O scheduler..."

# NVMe BFQ scheduler
sudo tee /etc/udev/rules.d/60-ioschedulers.rules << 'EOF'
# Set BFQ scheduler for NVMe devices to ensure I/O fairness
ACTION=="add|change", KERNEL=="nvme[0-9]*", ATTR{queue/scheduler}="bfq"
EOF

echo "Creating monitoring services..."

# PSI monitor timer
sudo tee /etc/systemd/system/psi-monitor.timer << 'EOF'
[Unit]
Description=Run PSI monitor every minute
Requires=psi-monitor.service

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min
Persistent=true

[Install]
WantedBy=timers.target
EOF

# PSI monitor service
sudo tee /etc/systemd/system/psi-monitor.service << 'EOF'
[Unit]
Description=PSI Monitor
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/bash -c 'echo "$(date):" >> /var/log/psi.log && echo "Memory: $(cat /proc/pressure/memory)" >> /var/log/psi.log && echo "I/O: $(cat /proc/pressure/io)" >> /var/log/psi.log && echo "CPU: $(cat /proc/pressure/cpu)" >> /var/log/psi.log && echo "---" >> /var/log/psi.log'
User=root
Group=root
EOF

# NVMe temperature monitor timer
sudo tee /etc/systemd/system/nvme-temp-monitor.timer << 'EOF'
[Unit]
Description=Run NVMe temperature monitor every 5 minutes
Requires=nvme-temp-monitor.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
EOF

# NVMe temperature monitor service
sudo tee /etc/systemd/system/nvme-temp-monitor.service << 'EOF'
[Unit]
Description=NVMe Temperature Monitor
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/bash -c 'echo "$(date): $(nvme smart-log /dev/nvme0n1 | grep temperature)" >> /var/log/nvme-temp.log'
User=root
Group=root
EOF

echo "Enabling services..."
sudo systemctl enable earlyoom
sudo systemctl enable sysstat
sudo systemctl enable psi-monitor.timer
sudo systemctl enable nvme-temp-monitor.timer

echo "Applying configurations..."
sudo systemctl daemon-reload
sudo sysctl --system
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "Starting services..."
sudo systemctl start earlyoom
sudo systemctl start sysstat
sudo systemctl start psi-monitor.timer
sudo systemctl start nvme-temp-monitor.timer

echo "Configuration complete!"
echo "Check status with:"
echo "  systemctl status earlyoom"
echo "  systemctl list-timers | grep -E '(psi|nvme)'"
echo "  cat /sys/block/nvme0n1/queue/scheduler"
echo "  free -h"
echo "  swapon --show"
```

## 9. Verification Commands

After applying all configurations, verify everything is working:

```bash
# Check systemd version
systemctl --version

# Check OOM protection
systemctl status earlyoom
systemctl status systemd-oomd

# Check memory and swap
free -h
swapon --show
cat /proc/sys/vm/swappiness

# Check I/O scheduler
cat /sys/block/nvme0n1/queue/scheduler

# Check monitoring timers
systemctl list-timers | grep -E "(psi|nvme)"

# Check logs
sudo tail -f /var/log/psi.log
sudo tail -f /var/log/nvme-temp.log

# Check SysRq
cat /proc/sys/kernel/sysrq

# Check slice configurations
systemctl show machine.slice | grep -E "(MemoryHigh|MemoryMax|IOWeight|CPUQuota)"
systemctl show graphical.slice | grep IOWeight
```

## 10. Notes and Future Considerations

1. **systemd Version**: Currently running systemd 257. Some features like `IOPressureLimit` require systemd ≥ 258.

2. **Hardware Specific**: CPU quota is set for 12-thread system (900% = 9 threads, leaving 3 free). Adjust for different hardware.

3. **Memory Configuration**: Based on 24GB RAM system. Memory percentages may need adjustment for different RAM sizes.

4. **Monitoring Logs**: PSI logs are written to `/var/log/psi.log` and NVMe temperature to `/var/log/nvme-temp.log`. Consider log rotation if needed.

5. **Build Containers**: The configuration mentions build containers but none were found currently configured. Add slice configurations for build/container workloads as needed.

6. **SSH Access**: SSH is currently disabled. Enable if remote emergency access is required.

---

This configuration creates a freeze-resistant Fedora development workstation that prioritizes desktop responsiveness while allowing intensive background tasks to run with controlled resource usage.
