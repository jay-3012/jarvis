"""Desktop Agent - Connects to Central Server via WebSocket."""

import asyncio
import websockets
import json
import structlog
import os
from datetime import datetime

logger = structlog.get_logger()


class DesktopAgent:
    """Desktop agent that connects to Central Server."""
    
    def __init__(self, device_id: str, server_url: str = "ws://localhost:8000/ws"):
        self.device_id = device_id
        self.server_url = f"{server_url}?device_id={device_id}"
        self.websocket = None
        self.running = False
        
    async def connect(self):
        """Connect to Central Server via WebSocket."""
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.running = True
            logger.info("Connected to Central Server", device_id=self.device_id)
            return True
        except Exception as e:
            logger.error("Failed to connect to Central Server", error=str(e))
            return False
    
    async def send_ping(self):
        """Send heartbeat ping to server."""
        if self.websocket:
            message = {
                "type": "ping",
                "device_id": self.device_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.websocket.send(json.dumps(message))
            logger.debug("Ping sent")
    
    async def send_response(self, command_id: str, status: str, data=None, error=None):
        """Send command response to server."""
        if self.websocket:
            message = {
                "type": "response",
                "command_id": command_id,
                "status": status,
                "data": data,
                "error": error,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.websocket.send(json.dumps(message))
            logger.info("Response sent", command_id=command_id, status=status)
    
    async def handle_command(self, message: dict):
        """Handle incoming command from server."""
        command_id = message.get("command_id")
        action = message.get("action")
        params = message.get("params", {})
        
        logger.info("Command received", command_id=command_id, action=action)
        
        try:
            result_data = None
            status = "success"
            error_msg = None

            # Route actions to Skills
            if action == "open_app":
                from layers.skills.app_launcher import AppLauncher
                skill = AppLauncher()
                msg = await skill.execute(params)
                result_data = {"message": msg}
                
            elif action == "run_command":
                from layers.skills.system_commander import SystemCommander
                skill = SystemCommander()
                msg = await skill.execute(params)
                result_data = {"output": msg}
                
            elif action == "test_command":
                # echo for testing
                result_data = params
                
            else:
                status = "error"
                error_msg = f"Unknown action: {action}"
                logger.warning(error_msg)

            # Send response
            await self.send_response(command_id, status, data=result_data, error=error_msg)
            
        except Exception as e:
            logger.error("Command execution failed", command_id=command_id, error=str(e))
            await self.send_response(command_id, "error", error=str(e))
    
    async def handle_message(self, message: dict):
        """Route incoming message to appropriate handler."""
        message_type = message.get("type")
        
        if message_type == "pong":
            logger.debug("Pong received")
        elif message_type == "command":
            await self.handle_command(message)
        elif message_type == "notification":
            logger.info("Notification received", message=message.get("message"))
        elif message_type == "error":
            logger.error("Error from server", error=message.get("error_message"))
        else:
            logger.warning("Unknown message type", type=message_type)
    
    async def listen_loop(self):
        """Main message listening loop."""
        try:
            while self.running:
                message_str = await self.websocket.recv()
                message = json.loads(message_str)
                await self.handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed")
            self.running = False
        except Exception as e:
            logger.error("Listen loop error", error=str(e))
            self.running = False
    
    async def heartbeat_loop(self):
        """Send periodic heartbeats."""
        while self.running:
            await asyncio.sleep(30)  # Send ping every 30 seconds
            if self.running:
                await self.send_ping()
    
    async def run(self):
        """Run the desktop agent."""
        if await self.connect():
            # Start heartbeat and listen loops concurrently
            await asyncio.gather(
                self.heartbeat_loop(),
                self.listen_loop()
            )
        else:
            logger.error("Failed to start agent - connection failed")
    
    async def stop(self):
        """Stop the agent and close connection."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
        logger.info("Agent stopped")


async def main():
    """Main entry point for desktop agent."""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    device_id = os.getenv("DEVICE_ID", "windows-laptop")
    
    # Try to get full URL first
    server_url = os.getenv("CENTRAL_SERVER_URL")
    
    # If not set, construct from host and port
    if not server_url:
        host = os.getenv("CENTRAL_SERVER_HOST", "localhost")
        port = os.getenv("CENTRAL_SERVER_PORT", "8000")
        server_url = f"ws://{host}:{port}/ws"
    
    agent = DesktopAgent(device_id, server_url)
    
    try:
        await agent.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await agent.stop()


if __name__ == "__main__":
    from utils.logging import configure_logging
    configure_logging()
    
    logger.info("Starting Desktop Agent...")
    asyncio.run(main())
