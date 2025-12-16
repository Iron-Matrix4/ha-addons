"""
Main entry point for Jarvis Home Assistant Add-on.
Runs both Wyoming protocol server and HTTP API server concurrently.
"""
import asyncio
import logging
import sys

from wyoming_handler import run_wyoming_server
from api_server import run_http_server
from conversation import JarvisConversation
from memory import Memory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

async def run_servers():
    """Run both Wyoming and HTTP servers concurrently."""
    logger.info("=" * 60)
    logger.info("J.A.R.V.I.S. - Just A Rather Very Intelligent System")
    logger.info("Starting Home Assistant Add-on...")
    logger.info("=" * 60)
    
    # Initialize memory (shared between servers)
    memory = Memory(db_path="/data/jarvis_memory.db")
    logger.info(f"Memory stats: {memory.get_stats()}")
    
    # Initialize Jarvis brain (shared between servers)
    jarvis = JarvisConversation(memory=memory)
    
    # Run both servers concurrently
    try:
        await asyncio.gather(
            run_wyoming_server(host="0.0.0.0", port=10400, jarvis=jarvis),
            run_http_server(jarvis=jarvis, host="0.0.0.0", port=10401)
        )
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        memory.close()

def main():
    """Main entry point."""
    try:
        asyncio.run(run_servers())
    except Exception as e:
        logger.error(f"Failed to start servers: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
