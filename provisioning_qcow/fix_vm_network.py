#!/usr/bin/env python3
"""
VM Network Fix Script

Restarts libvirt networking and ensures VM connectivity after resume from saved state.
Handles the common networking issues that occur when VMs are suspended/resumed.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


class VMNetworkFixer:
    def __init__(self, vm_name="ubuntu24.04", network_name="default"):
        self.vm_name = vm_name
        self.network_name = network_name
        self.sudo_prefix = [] if self._is_root() else ["sudo"]

    def _is_root(self):
        """Check if running as root."""
        return subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.strip() == "0"

    def _run_command(self, cmd, check=True, capture_output=True):
        """Run a command with proper error handling."""
        full_cmd = self.sudo_prefix + cmd if any(x in cmd for x in ["virsh", "systemctl"]) else cmd
        try:
            result = subprocess.run(full_cmd, capture_output=capture_output, text=True, check=check)
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {' '.join(full_cmd)}")
            print(f"   Error: {e.stderr if e.stderr else e.stdout}")
            raise

    def check_vm_exists(self):
        """Verify the VM exists."""
        print(f"🔍 Checking if VM '{self.vm_name}' exists...")
        try:
            result = self._run_command(["virsh", "dominfo", self.vm_name])
            print(f"✅ VM '{self.vm_name}' found")
            return True
        except subprocess.CalledProcessError:
            print(f"❌ VM '{self.vm_name}' not found")
            return False

    def get_vm_state(self):
        """Get current VM state."""
        result = self._run_command(["virsh", "domstate", self.vm_name])
        return result.stdout.strip()

    def restart_network(self, vm_running=False):
        """Restart the libvirt network, handling running VMs properly."""
        print(f"📡 Checking libvirt network '{self.network_name}'...")
        
        # Check if network exists
        try:
            self._run_command(["virsh", "net-info", self.network_name])
        except subprocess.CalledProcessError:
            print(f"❌ Network '{self.network_name}' not found")
            return False

        # Check if network is active
        try:
            result = self._run_command(["virsh", "net-list"], check=False)
            network_active = self.network_name in result.stdout and "active" in result.stdout
        except subprocess.CalledProcessError:
            network_active = False

        # If VM is running and network is active, check if bridge is working
        if vm_running and network_active:
            bridge_name = f"virbr0"  # Default bridge name
            try:
                result = self._run_command(["ip", "link", "show", bridge_name], check=False)
                if "LOWER_UP" in result.stdout:
                    print(f"✅ Network '{self.network_name}' and bridge are working")
                    return True
                else:
                    print(f"⚠️  Bridge '{bridge_name}' is not properly connected")
                    return self._fix_bridge_connection()
            except:
                print(f"⚠️  Could not check bridge status")

        # If we get here, we need to restart the network
        if vm_running:
            print(f"⚠️  WARNING: Restarting network while VM is running may cause connectivity issues")

        if network_active:
            print(f"   Stopping network '{self.network_name}'...")
            self._run_command(["virsh", "net-destroy", self.network_name])

        # Start network
        print(f"   Starting network '{self.network_name}'...")
        self._run_command(["virsh", "net-start", self.network_name])
        print(f"✅ Network '{self.network_name}' restarted")
        return True

    def _fix_bridge_connection(self):
        """Fix bridge connection issues when VM is running."""
        print(f"🔧 Fixing bridge connection...")
        
        # Get VM's virtual interfaces
        try:
            result = self._run_command(["virsh", "domiflist", self.vm_name])
            interfaces = []
            for line in result.stdout.split('\n')[2:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 1:
                        # The target (interface name) might be in different positions
                        # Look for vnet* pattern
                        for part in parts:
                            if part.startswith('vnet'):
                                interfaces.append(part)
                                break
        except:
            # Fallback: find vnet interfaces manually
            result = self._run_command(["ip", "link", "show"], check=False)
            interfaces = []
            for line in result.stdout.split('\n'):
                if 'vnet' in line and ':' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        iface_name = parts[1].strip().split('@')[0]
                        if iface_name.startswith('vnet'):
                            interfaces.append(iface_name)
        
        if not interfaces:
            print(f"⚠️  No virtual interfaces found for VM")
            return False
            
        print(f"   Found VM interfaces: {', '.join(interfaces)}")
        
        # Re-attach interfaces to bridge
        bridge_name = "virbr0"
        success = False
        
        for iface in interfaces:
            try:
                print(f"   Attaching {iface} to bridge {bridge_name}...")
                self._run_command(["ip", "link", "set", iface, "master", bridge_name])
                success = True
            except subprocess.CalledProcessError as e:
                print(f"   ⚠️  Failed to attach {iface}: {e}")
        
        if success:
            print(f"✅ Bridge connection fixed")
            time.sleep(2)  # Give bridge time to come up
        
        return success

    def start_vm_if_needed(self):
        """Start VM if it's not running."""
        state = self.get_vm_state()
        print(f"🔍 VM state: {state}")
        
        if state == "running":
            print(f"✅ VM '{self.vm_name}' is already running")
            return True
        elif state in ["shut off", "crashed"]:
            print(f"🔄 Starting VM '{self.vm_name}'...")
            self._run_command(["virsh", "start", self.vm_name])
            print(f"✅ VM '{self.vm_name}' started")
            return True
        elif state == "saved":
            print(f"🔄 Resuming VM '{self.vm_name}' from saved state...")
            self._run_command(["virsh", "resume", self.vm_name])
            print(f"✅ VM '{self.vm_name}' resumed")
            return True
        else:
            print(f"⚠️  Unknown VM state: {state}")
            return False

    def wait_for_vm_network(self, timeout=30):
        """Wait for VM to get an IP address."""
        print(f"⏳ Waiting for VM network (timeout: {timeout}s)...")
        
        for attempt in range(1, timeout + 1):
            try:
                result = self._run_command(["virsh", "domifaddr", self.vm_name, "--source", "lease"], check=False)
                if result.returncode == 0 and "ipv4" in result.stdout:
                    print("✅ VM network is ready!")
                    # Extract and display IP
                    lines = result.stdout.strip().split('\n')
                    for line in lines[2:]:  # Skip header lines
                        if line.strip() and "ipv4" in line:
                            parts = line.split()
                            if len(parts) >= 4:
                                ip = parts[3].split('/')[0]
                                print(f"   VM IP: {ip}")
                                return ip
                    return True
            except subprocess.CalledProcessError:
                pass
            
            if attempt % 5 == 0:
                print(f"   Attempt {attempt}/{timeout} - still waiting...")
            time.sleep(1)
        
        print("⚠️  Timeout waiting for VM network")
        return False

    def test_connectivity(self, ip=None):
        """Test connectivity to the VM."""
        if not ip:
            # Try to get IP from lease
            try:
                result = self._run_command(["virsh", "domifaddr", self.vm_name, "--source", "lease"])
                for line in result.stdout.split('\n'):
                    if "ipv4" in line:
                        ip = line.split()[3].split('/')[0]
                        break
            except:
                pass
        
        if ip:
            print(f"🏓 Testing connectivity to {ip}...")
            try:
                result = self._run_command(["ping", "-c", "3", "-W", "2", ip], check=False)
                if result.returncode == 0:
                    print("✅ VM is reachable via ping")
                    return True
                else:
                    print("⚠️  VM is not responding to ping")
            except:
                print("⚠️  Could not test connectivity")
        
        return False

    def fix_network(self):
        """Main function to fix VM networking."""
        print("🚀 Starting VM network fix process...")
        print(f"   VM: {self.vm_name}")
        print(f"   Network: {self.network_name}")
        print()

        # Step 1: Check VM exists
        if not self.check_vm_exists():
            return False

        # Step 2: Check if VM is currently running
        vm_was_running = self.get_vm_state() == "running"
        
        # Step 3: Restart libvirt network (with awareness of running VMs)
        if not self.restart_network(vm_running=vm_was_running):
            return False

        # Step 4: Start VM if needed
        if not self.start_vm_if_needed():
            return False

        # Step 5: Wait for VM network
        vm_ip = self.wait_for_vm_network()
        if not vm_ip:
            print("❌ Failed to get VM IP address")
            return False

        # Step 6: Test connectivity and fix if needed
        if not self.test_connectivity(vm_ip):
            print("🔧 Connectivity test failed, attempting bridge fix...")
            if self._fix_bridge_connection():
                print("⏳ Waiting after bridge fix...")
                time.sleep(5)
                self.test_connectivity(vm_ip)
            else:
                print("⚠️  Bridge fix failed, but VM may still be accessible")

        print()
        print("🎉 VM network fix completed!")
        print(f"   You can now SSH to: {vm_ip}")
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Fix VM networking issues after resume from saved state",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                        # Fix ubuntu24.04 VM with default network
  %(prog)s --vm myvm              # Fix specific VM
  %(prog)s --vm myvm --network br0  # Fix VM with custom network
  %(prog)s --test-only            # Just test current connectivity
        """
    )
    
    parser.add_argument(
        "--vm", "-v",
        default="ubuntu24.04",
        help="Name of the VM to fix (default: ubuntu24.04)"
    )
    
    parser.add_argument(
        "--network", "-n",
        default="default",
        help="Name of the libvirt network (default: default)"
    )
    
    parser.add_argument(
        "--test-only", "-t",
        action="store_true",
        help="Only test connectivity, don't fix anything"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds to wait for VM network (default: 30)"
    )

    args = parser.parse_args()

    # Create fixer instance
    fixer = VMNetworkFixer(vm_name=args.vm, network_name=args.network)

    try:
        if args.test_only:
            print("🧪 Testing connectivity only...")
            if not fixer.check_vm_exists():
                sys.exit(1)
            
            state = fixer.get_vm_state()
            if state != "running":
                print(f"❌ VM is not running (state: {state})")
                sys.exit(1)
            
            ip = fixer.wait_for_vm_network(timeout=5)
            if ip and fixer.test_connectivity(ip):
                print("✅ VM networking is working correctly")
                sys.exit(0)
            else:
                print("❌ VM networking issues detected")
                sys.exit(1)
        else:
            # Full network fix
            success = fixer.fix_network()
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()