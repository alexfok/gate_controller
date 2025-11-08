"""Main entry point for gate controller service."""

import asyncio
import argparse
import signal
import sys

from .config.config import Config
from .core.controller import GateController
from .utils.logger import get_logger


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Gate Controller - Automated gate control with BLE token detection",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config/config.yaml',
        help='Configuration file path (default: config/config.yaml)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


async def main():
    """Main function."""
    args = parse_arguments()
    
    # Load configuration
    config = Config(args.config)
    
    if args.verbose:
        config.config['logging']['level'] = 'DEBUG'
    
    logger = get_logger(__name__, config.log_level, config.log_file)
    logger.info("="*60)
    logger.info("Gate Controller Starting")
    logger.info("="*60)
    
    # Create controller
    controller = GateController(config)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        asyncio.create_task(controller.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start controller
    try:
        await controller.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await controller.stop()
    
    logger.info("Gate Controller stopped")


if __name__ == '__main__':
    asyncio.run(main())

