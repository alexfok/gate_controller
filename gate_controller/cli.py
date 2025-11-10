"""Command-line interface for gate controller management."""

import asyncio
import argparse
import sys
from tabulate import tabulate

from .config.config import Config
from .core.controller import GateController
from .ble.scanner import BLEScanner
from .utils.logger import get_logger


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Gate Controller CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config/config.yaml',
        help='Configuration file path (default: config/config.yaml)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Register token command
    register_parser = subparsers.add_parser('register-token', help='Register a new BLE token')
    register_parser.add_argument('--uuid', required=True, help='Token UUID (BLE address)')
    register_parser.add_argument('--name', required=True, help='User-friendly name')
    
    # Unregister token command
    unregister_parser = subparsers.add_parser('unregister-token', help='Unregister a BLE token')
    unregister_parser.add_argument('--uuid', required=True, help='Token UUID')
    
    # List tokens command
    list_parser = subparsers.add_parser('list-tokens', help='List all registered tokens')
    
    # Scan for devices command
    scan_parser = subparsers.add_parser('scan-devices', help='Scan for nearby BLE devices')
    scan_parser.add_argument('--duration', type=int, default=10, help='Scan duration in seconds')
    
    # Open gate command
    open_parser = subparsers.add_parser('open-gate', help='Open the gate')
    
    # Close gate command
    close_parser = subparsers.add_parser('close-gate', help='Close the gate')
    
    # Check status command
    status_parser = subparsers.add_parser('check-status', help='Check gate status')
    
    # Refresh token command
    refresh_token_parser = subparsers.add_parser('refresh-token', help='Refresh C4 director token')
    
    # Remove credentials command
    remove_creds_parser = subparsers.add_parser('remove-credentials', help='Remove username/password from config (token-only mode)')
    
    return parser.parse_args()


async def cmd_register_token(config: Config, args):
    """Register a new token."""
    controller = GateController(config)
    
    success = controller.register_token(args.uuid, args.name)
    
    if success:
        print(f"✅ Token registered successfully: {args.name} ({args.uuid})")
    else:
        print(f"❌ Failed to register token (may already exist)")
        sys.exit(1)


async def cmd_unregister_token(config: Config, args):
    """Unregister a token."""
    controller = GateController(config)
    
    success = controller.unregister_token(args.uuid)
    
    if success:
        print(f"✅ Token unregistered successfully: {args.uuid}")
    else:
        print(f"❌ Failed to unregister token (not found)")
        sys.exit(1)


async def cmd_list_tokens(config: Config, args):
    """List all registered tokens with detection status."""
    controller = GateController(config)
    
    tokens = controller.get_registered_tokens()
    
    if not tokens:
        print("No tokens registered")
        return
    
    print(f"\nScanning for registered tokens (5s)...")
    
    # Do a quick scan to see which tokens are currently detected
    scanner = BLEScanner(registered_tokens=tokens)
    detected = await scanner.scan_once(duration=5.0)
    detected_uuids = {d['uuid'].lower() for d in detected}
    
    print(f"\nRegistered Tokens ({len(tokens)}):")
    print("="*80)
    
    table_data = []
    for i, token in enumerate(tokens):
        status = "🟢 In Range" if token['uuid'].lower() in detected_uuids else "⚪ Not Detected"
        table_data.append([i+1, token['name'], token['uuid'], status])
    
    print(tabulate(table_data, headers=['#', 'Name', 'UUID', 'Status'], tablefmt='simple'))


async def cmd_scan_devices(config: Config, args):
    """Scan for nearby BLE devices."""
    print(f"Scanning for BLE devices and iBeacons ({args.duration}s)...")
    
    scanner = BLEScanner(registered_tokens=[])
    devices = await scanner.list_nearby_devices(duration=args.duration)
    
    if not devices:
        print("No devices found")
        return
    
    # Separate iBeacons and regular devices
    beacons = [d for d in devices if d.get('type') == 'iBeacon']
    regular = [d for d in devices if d.get('type') != 'iBeacon']
    
    if beacons:
        print(f"\n📡 Found {len(beacons)} iBeacon(s):")
        print("="*120)
        
        beacon_data = []
        for i, dev in enumerate(beacons):
            # Format signal quality
            rssi = dev.get('rssi', 0)
            if rssi >= -60:
                signal = "🟢 Excellent"
            elif rssi >= -70:
                signal = "🟡 Good"
            elif rssi >= -80:
                signal = "🟠 Fair"
            elif rssi >= -90:
                signal = "🔴 Weak"
            else:
                signal = "⚫ Very Weak"
            
            distance = dev.get('distance', -1)
            dist_str = f"~{distance}m" if distance > 0 else "Unknown"
            
            beacon_data.append([
                i+1,
                dev['name'],
                dev['uuid'],
                dev['major'],
                dev['minor'],
                f"{rssi} dBm",
                dist_str,
                signal
            ])
        
        print(tabulate(beacon_data, 
                      headers=['#', 'Name', 'UUID', 'Major', 'Minor', 'RSSI', 'Distance', 'Signal'], 
                      tablefmt='simple'))
        print("\n💡 To register an iBeacon, use its UUID:")
        print("   python3 -m gate_controller.cli register-token --uuid <UUID> --name <name>")
    
    if regular:
        print(f"\n📱 Found {len(regular)} regular BLE device(s):")
        print("="*100)
        
        table_data = []
        for i, dev in enumerate(regular):
            rssi = dev.get('rssi', 0)
            distance = dev.get('distance', -1)
            dist_str = f"~{distance}m" if distance > 0 else "Unknown"
            
            # Format signal quality
            if rssi >= -60:
                signal = "🟢 Excellent"
            elif rssi >= -70:
                signal = "🟡 Good"
            elif rssi >= -80:
                signal = "🟠 Fair"
            elif rssi >= -90:
                signal = "🔴 Weak"
            else:
                signal = "⚫ Very Weak"
            
            table_data.append([i+1, dev['name'], dev['address'], f"{rssi} dBm", dist_str, signal])
        
        print(tabulate(table_data, headers=['#', 'Name', 'Address', 'RSSI', 'Distance', 'Signal'], tablefmt='simple'))
        print("\n💡 To register a device, use its address:")
        print("   python3 -m gate_controller.cli register-token --uuid <address> --name <name>")


async def cmd_open_gate(config: Config, args):
    """Open the gate."""
    controller = GateController(config)
    
    try:
        await controller.c4_client.connect()
        success = await controller.open_gate("Manual CLI command")
        
        if success:
            print("✅ Gate opened successfully")
        else:
            print("❌ Failed to open gate")
            sys.exit(1)
    finally:
        await controller.c4_client.disconnect()


async def cmd_close_gate(config: Config, args):
    """Close the gate."""
    controller = GateController(config)
    
    try:
        await controller.c4_client.connect()
        success = await controller.close_gate("Manual CLI command")
        
        if success:
            print("✅ Gate closed successfully")
        else:
            print("❌ Failed to close gate")
            sys.exit(1)
    finally:
        await controller.c4_client.disconnect()


async def cmd_check_status(config: Config, args):
    """Check gate status."""
    controller = GateController(config)
    
    try:
        await controller.c4_client.connect()
        status = await controller.check_gate_status()
        
        print("\nGate Status:")
        print("="*60)
        print(f"State: {status['gate_state']}")
        print(f"Last Opened: {status['last_open_time'] or 'Never'}")
        print(f"Session Active: {status['session_active']}")
        print(f"\nControl4 Status: {status['c4_status']}")
    finally:
        await controller.c4_client.disconnect()


async def cmd_refresh_token(config: Config, args):
    """Refresh C4 director token."""
    controller = GateController(config)
    
    print("\nRefreshing C4 Director Token...")
    print("="*60)
    
    try:
        # Force full authentication
        await controller.c4_client.connect()
        
        # Token is already saved by the callback
        print(f"✅ Token refreshed successfully")
        print(f"✅ Controller: {controller.c4_client.cached_controller_name}")
        print(f"✅ Token saved to: {config.config_file}")
        print(f"\nNew token (first 50 chars): {controller.c4_client.cached_director_token[:50]}...")
        
    except Exception as e:
        print(f"❌ Failed to refresh token: {e}")
        raise
    finally:
        await controller.c4_client.disconnect()


async def cmd_remove_credentials(config: Config, args):
    """Remove username and password from config."""
    print("\n⚠️  Remove Credentials (Token-Only Mode)")
    print("="*60)
    
    if not config.director_token:
        print("❌ Cannot remove credentials: No director token cached")
        print("   Run 'refresh-token' first to cache the token")
        return
    
    print(f"Director token is cached: {config.director_token[:50]}...")
    print(f"Controller: {config.controller_name}")
    print()
    
    # Show current credentials status
    has_username = bool(config.c4_username)
    has_password = bool(config.c4_password)
    
    if not has_username and not has_password:
        print("✅ Already in token-only mode (no credentials in config)")
        return
    
    print(f"Current credentials:")
    print(f"  Username: {'✅ Present' if has_username else '❌ Not found'}")
    print(f"  Password: {'✅ Present' if has_password else '❌ Not found'}")
    print()
    
    response = input("Remove credentials from config? This enables token-only mode. [y/N]: ")
    
    if response.lower() == 'y':
        removed = config.remove_credentials()
        if removed:
            print()
            print("✅ Credentials removed successfully")
            print("✅ Token-only mode enabled")
            print()
            print("⚠️  If the token expires, you will need to:")
            print("   1. Manually add credentials back to config.yaml")
            print("   2. Run 'refresh-token' to get a new token")
        else:
            print("⚠️  No credentials found to remove")
    else:
        print("Cancelled - credentials kept in config")


async def main():
    """Main CLI function."""
    args = parse_arguments()
    
    if not args.command:
        print("Error: No command specified. Use --help for usage information.")
        sys.exit(1)
    
    # Load configuration
    config = Config(args.config)
    logger = get_logger(__name__, 'INFO')
    
    # Execute command
    commands = {
        'register-token': cmd_register_token,
        'unregister-token': cmd_unregister_token,
        'list-tokens': cmd_list_tokens,
        'scan-devices': cmd_scan_devices,
        'open-gate': cmd_open_gate,
        'close-gate': cmd_close_gate,
        'check-status': cmd_check_status,
        'refresh-token': cmd_refresh_token,
        'remove-credentials': cmd_remove_credentials,
    }
    
    handler = commands.get(args.command)
    if handler:
        try:
            await handler(config, args)
        except Exception as e:
            logger.error(f"Command failed: {e}", exc_info=True)
            sys.exit(1)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

