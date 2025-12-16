"""
Wyoming protocol handler for Jarvis conversation agent.
Simplified implementation using wyoming.event base classes.
"""
import asyncio
import logging
from functools import partial
from typing import Optional

from wyoming.info import AsrModel, AsrProgram, Attribution, Info
from wyoming.server import AsyncServer
from wyoming.event import Event, async_read_event, async_write_event

from conversation import JarvisConversation
from memory import Memory

logger = logging.getLogger(__name__)

class JarvisWyomingHandler:
    """Handler for Wyoming protocol events - simplified for conversation."""
    
    def __init__(self, jarvis: JarvisConversation):
        """
        Initialize Wyoming handler.
        
        Args:
            jarvis: JarvisConversation instance
        """
        self.jarvis = jarvis
    
    async def handle_event(self, event):
        """
        Handle incoming Wyoming protocol events.
        
        Args:
            event: Wyoming event
            
        Returns:
            Wyoming response event or None
        """
        logger.debug(f"Received event: {event}")
        
        # For now, handle generic text events
        # Wyoming will send us text from STT, we return text for TTS
        if hasattr(event, 'text') and event.text:
            text = event.text
            logger.info(f"User said: {text}")
            
            try:
                # Process through Jarvis brain
                response = self.jarvis.process(text)
                logger.info(f"Jarvis: {response}")
                
                # Create response event with text
                response_event = Event(type="text", data={"text": response})
                return response_event
            
            except Exception as e:
                logger.error(f"Error processing: {e}", exc_info=True)
                error_response = Event(type="text", data={"text": "I encountered an error, Sir."})
                return error_response
        
        return None


async def run_wyoming_server(jarvis: JarvisConversation, host: str = "0.0.0.0", port: int = 10400):
    """
    Run the Wyoming protocol server for Jarvis.
    
    Args:
        jarvis: JarvisConversation instance
        host: Host to bind to
        port: Port to listen on
    """
    logger.info(f"Starting Jarvis Wyoming server on {host}:{port}")
    
    # Create handler
    handler = JarvisWyomingHandler(jarvis=jarvis)
    
    # Create info for service advertising
    wyoming_info = Info(
        asr=[
            AsrProgram(
                name="Jarvis AI",
                description="J.A.R.V.I.S. conversation agent",
                attribution=Attribution(
                    name="Jarvis AI",
                    url="https://github.com/yourusername/jarvis-ai",
                ),
                installed=True,
                version="1.0.0",
                models=[
                    AsrModel(
                        name="gemini-2.0-flash",
                        description="Gemini 2.0 Flash model",
                        attribution=Attribution(
                            name="Google",
                            url="https://ai.google.dev/gemini-api",
                        ),
                        installed=True,
                        version="2.0",
                        languages=["en"],
                    )
                ],
            )
        ],
    )
    
    # Create server
    server =AsyncServer.from_uri(f"tcp://{host}:{port}")
    
    logger.info("Jarvis conversation agent ready!")
    logger.info("Waiting for connections from Home Assistant...")
    
    try:
        await server.run(
            partial(handle_client, handler=handler, wyoming_info=wyoming_info)
        )
    except KeyboardInterrupt:
        logger.info("Shutting down Wyoming server...")


async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    handler: JarvisWyomingHandler,
    wyoming_info: Info,
):
    """
    Handle a client connection.
    
    Args:
        reader: Stream reader
        writer: Stream writer
        handler: JarvisWyomingHandler instance
        wyoming_info: Wyoming info object
    """
    client_address = writer.get_extra_info("peername")
    logger.info(f"Client connected: {client_address}")
    
    try:
        # Send info on connect
        await async_write_event(wyoming_info.event(), writer)
        
        # Process events
        while True:
            event = await async_read_event(reader)
            
            if event is None:
                logger.debug("Client disconnected")
                break
            
            # Handle event
            response = await handler.handle_event(event)
            
            if response is not None:
                await async_write_event(response, writer)
                await writer.drain()
    
    except Exception as e:
        logger.error(f"Error handling client: {e}", exc_info=True)
    
    finally:
        writer.close()
        await writer.wait_closed()
        logger.info(f"Client disconnected: {client_address}")
