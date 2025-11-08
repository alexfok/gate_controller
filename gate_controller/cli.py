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
    """List all registered tokens."""
    controller = GateController(config)
    
    tokens = controller.get_registered_tokens()
    
    if not tokens:
        print("No tokens registered")
        return
    
    print(f"\nRegistered Tokens ({len(tokens)}):")
    print("="*60)
    
    table_data = [[i+1, token['name'], token['uuid']] 
                  for i, token in enumerate(tokens)]
    
    print(tabulate(table_data, headers=['#', 'Name', 'UUID'], tablefmt='simple'))


async def cmd_scan_devices(config: Config, args):
    """Scan for nearby BLE devices."""
    print(f"Scanning for BLE devices ({args.duration}s)...")
    
    scanner = BLEScanner(registered_tokens=[])
    devices = await scanner.list_nearby_devices(duration=args.duration)
    
    if not devices:
        print("No devices found")
        return
    
    print(f"\nFound {len(devices)} devices:")
    print("="*80)
    
    table_data = [[i+1, dev['name'], dev['address'], dev['rssi']] 
                  for i, dev in enumerate(devices)]
    
    print(tabulate(table_data, headers=['#', 'Name', 'Address', 'RSSI'], tablefmt='simple'))
    print("\nTo register a device, use: gate-controller register-token --uuid <address> --name <name>")


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

