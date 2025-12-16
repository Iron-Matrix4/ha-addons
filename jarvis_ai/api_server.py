"""
HTTP API server for Jarvis conversation endpoint.
Allows custom HA integration to communicate with Jarvis backend.
"""
import asyncio
import logging
from aiohttp import web
from conversation import JarvisConversation
from memory import Memory

logger = logging.getLogger(__name__)

class JarvisHTTPAPI:
    """HTTP API server for Jarvis conversation."""
    
    def __init__(self, jarvis: JarvisConversation):
        """Initialize API with Jarvis instance."""
        self.jarvis = jarvis
        self.app = web.Application()
        self.app.router.add_post('/conversation', self.handle_conversation)
        self.app.router.add_get('/health', self.handle_health)
    
    async def handle_conversation(self, request):
        """
        Handle conversation request.
        
        Expected JSON:
        {
            "text": "user input text",
            "conversation_id": "optional_id"
        }
        
        Returns:
        {
            "response": "Jarvis response text"
        }
        """
        try:
            data = await request.json()
            text = data.get('text', '')
            
            if not text:
                return web.json_response(
                    {'error': 'No text provided'},
                    status=400
                )
            
            logger.info(f"Processing: {text}")
            
            # Process through Jarvis
            response = self.jarvis.process(text)
            
            logger.info(f"Response: {response}")
            
            return web.json_response({'response': response})
        
        except Exception as e:
            logger.error(f"Error processing conversation: {e}", exc_info=True)
            return web.json_response(
                {'error': str(e)},
                status=500
            )
    
    async def handle_health(self, request):
        """Health check endpoint."""
        return web.json_response({'status': 'ok'})
    
    def run(self, host='0.0.0.0', port=10401):
        """Run the HTTP server."""
        logger.info(f"Starting Jarvis HTTP API on {host}:{port}")
        web.run_app(self.app, host=host, port=port)


async def run_http_server(jarvis: JarvisConversation, host='0.0.0.0', port=10401):
    """
    Run HTTP API server for Jarvis.
    
    Args:
        jarvis: JarvisConversation instance
        host: Host to bind to
        port: Port to listen on
    """
    api = JarvisHTTPAPI(jarvis)
    
    logger.info(f"Jarvis HTTP API ready on {host}:{port}")
    logger.info("Custom integration can now connect to Jarvis")
    
    # Run the web server
    runner = web.AppRunner(api.app)
    await runner.setup()
    
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Shutting down HTTP API...")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    import asyncio
    from config_helper import GEMINI_API_KEY
    
    # Initialize for testing
    memory = Memory(db_path="/data/jarvis_memory.db")
    jarvis = JarvisConversation(memory=memory)
    
    asyncio.run(run_http_server(jarvis))
