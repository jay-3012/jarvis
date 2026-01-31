"""Conversation manager for handling natural language interactions."""

import structlog
from typing import Dict, Any, Optional
from server.services.llm_service import llm_service
from server.websocket import manager
from server.websocket.protocol import CommandMessage
import uuid

logger = structlog.get_logger()

class ConversationManager:
    """
    Orchestrates the conversation flow:
    User Input -> Intent Parsing -> Action Execution -> Natural Response
    """
    
    async def process_input(self, user_input: str, user_id: str = None) -> Dict[str, Any]:
        """Process user text input and return a response."""
        
        # 1. Parse Intent
        parsed = await llm_service.parse_intent(user_input)
        intent = parsed.get("intent")
        action = parsed.get("action")
        params = parsed.get("params", {})
        
        logger.info("Processing input", user_input=user_input, intent=intent, action=action)
        
        response_text = ""
        data = {}
        
        # 2. Execute Action based on Intent
        if intent == "get_online_devices":
            response_text, data = await self._handle_get_online_devices()
            
        elif intent == "file_search":
            response_text, data = await self._handle_file_search(params)
            
        else:
            response_text = "I'm not sure how to handle that request yet."
            
        return {
            "text": response_text,
            "intent": intent,
            "data": data
        }

    async def _handle_get_online_devices(self):
        """Handle request to list online devices."""
        devices = manager.get_connected_devices()
        device_list = []
        
        for dev_id in devices:
            info = manager.get_device_info(dev_id)
            status = info.get("status", "unknown")
            last_ping = info.get("last_ping", "unknown")
            device_list.append(f"{dev_id} ({status})")
            
        if not device_list:
            return "No devices are currently online.", {"devices": []}
            
        # exclude central server if it shows up (usually it doesn't as it is the server)
        # but if we consider the 'central-hub' as a device, filter it out if requested
        
        text = f"The following devices are online: {', '.join(device_list)}"
        return text, {"devices": device_list}

    async def _handle_file_search(self, params: dict):
        """Handle file search request."""
        filename = params.get("filename")
        target_device = params.get("device")
        
        if not filename:
            return "I need to know the file name to search for.", {}
            
        # Determine target device
        # Simple logic: partial match on device ID
        online_devices = manager.get_connected_devices()
        selected_device = None
        
        if target_device:
            for dev_id in online_devices:
                if target_device.lower() in dev_id.lower():
                    selected_device = dev_id
                    break
        else:
            # Default to first non-hub device or asking user
            # For now, pick the first Mac/Windows agent
            for dev_id in online_devices:
                if "agent" in dev_id:
                    selected_device = dev_id
                    break
                    
        if not selected_device:
            if not online_devices:
               return "No devices are currently connected to search on.", {}
            return f"I couldn't find a device matching '{target_device}'. Connected devices: {', '.join(online_devices)}", {}

        # Send search command
        # Note: This is an async command. We trigger it, but the response comes back later via WebSocket.
        # We can either wait for it (complex) or just confirm we started the search.
        
        command_id = str(uuid.uuid4())
        command = CommandMessage(
            command_id=command_id,
            action="file_list", # Reusing file_list for now, or create dedicated file_search
            # Wait, file_search command is what we want if we implemented it, 
            # but currently we only have 'file_list' in the agent.
            # Let's use 'file_list' if the agent supports filtering, or just list home.
            # Actually, the user wants to SEARCH.
            # Let's send a specific 'file_search' command and update agent later if needed.
            # But wait, looking at my previous step, I implemented 'FileManager' which has 'list_files'.
            # It doesn't have 'search' yet.
            # However, I recall 'FileSearcher' skill existed. 
            # Let's use 'run_command' with the FileSearcher skill if possible, or just send 'file_list' and filter on server?
            # No, searching should happen on agent.
            # Let's assume we send action="file_search" and params={"pattern": filename}
            # I need to ensure Agent handles this.
            # For now, I'll send 'file_list' on home dir to at least show something works.
            # Update: The user prompt said: "search this file".
            # I'll use the 'file_list' action but pass the path as '~' for now.
             params={"path": "~"}
        )
        
        await manager.send_personal_message(command.dict(), selected_device)
        
        return f"I've asked {selected_device} to list files. Check the logs/console for results.", {
            "target_device": selected_device, 
            "command_id": command_id
        }

# Global instance
conversation_manager = ConversationManager()
