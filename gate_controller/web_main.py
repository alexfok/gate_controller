"""
Main entry point for Gate Controller with Web Dashboard.
"""
import asyncio
import argparse
import sys
from pathlib import Path

from gate_controller.config.config import Config
from gate_controller.core.controller import GateController
from gate_controller.core.activity_log import ActivityLog
from gate_controller.web.server import DashboardServer
from gate_controller.utils.logger import get_logger
import uvicorn


async def run_controller_with_dashboard(config_path: str, host: str = "0.0.0.0", port: int = 8000):
    """
    Run the gate controller with web dashboard.
    
    Args:
        config_path: Path to configuration file
        host: Dashboard host
        port: Dashboard port
    """
    # Load configuration
    config = Config(config_path)
    logger = get_logger(__name__, config.log_level, config.log_file)
    
    logger.info("="*60)
    logger.info("Gate Controller with Web Dashboard Starting")
    logger.info("="*60)
    
    # Create activity log
    activity_log = ActivityLog()
    activity_log.log_info("System started", {"config": config_path})
    
    # Create controller
    controller = GateController(config, activity_log=activity_log)
    
    # Create dashboard server
    dashboard = DashboardServer(config, controller, activity_log)
    
    try:
        # Start controller in background
        logger.info("Starting gate controller...")
        controller_task = asyncio.create_task(controller.start())
        
        # Give controller time to initialize
        await asyncio.sleep(2)
        
        # Run dashboard server (this blocks)
        logger.info(f"Starting web dashboard on http://{host}:{port}")
        logger.info(f"Open your browser to view the dashboard")
        
        # Configure uvicorn
        config = uvicorn.Config(
            dashboard.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        # Run server
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("\nShutdown requested...")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        activity_log.log_error(str(e))
    finally:
        # Stop controller
        logger.info("Stopping gate controller...")
        await controller.stop()
        activity_log.log_info("System stopped")
        
        logger.info("="*60)
        logger.info("Gate Controller Stopped")
        logger.info("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Gate Controller with Web Dashboard")
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Dashboard host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Dashboard port (default: 8000)"
    )
    
    args = parser.parse_args()
    
    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Configuration file not found: {args.config}")
        print("Please create a configuration file or specify an existing one with --config")
        sys.exit(1)
    
    # Run controller with dashboard
    try:
        asyncio.run(run_controller_with_dashboard(args.config, args.host, args.port))
    except KeyboardInterrupt:
        print("\nShutdown complete")
        sys.exit(0)


if __name__ == "__main__":
    main()

