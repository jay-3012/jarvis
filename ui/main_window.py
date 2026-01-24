import flet as ft
import asyncio
from core.event_bus import internal_bus
from core.config import global_settings

class JarvisUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "JARVIS System Interface"
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "JARVIS System Interface"
        self.page.theme_mode = "dark"
        self.page.window_width = 500
        self.page.window_height = 800
        self.page.bgcolor = "#000000"  # Deep black background
        
        # UI Elements
        self.chat_list = ft.ListView(
            expand=True, 
            spacing=10, 
            auto_scroll=True,
            padding=20
        )
        
        # Arc Reactor (Visualizer)
        # Using a Container with gradients and animation
        self.reactor_core = ft.Container(
            width=150,
            height=150,
            bgcolor="cyan400",
            border_radius=75,
            alignment=ft.Alignment(0, 0),
            shadow=ft.BoxShadow(spread_radius=10, blur_radius=20, color="cyan200"),
            animate=ft.Animation(500, "easeInOut"),
        )
        
        self.reactor_outer = ft.Container(
            width=160,
            height=160,
            border=ft.border.all(5, "cyan700"),
            border_radius=80,
            content=self.reactor_core,
            alignment=ft.Alignment(0, 0),
            animate_scale=ft.Animation(500, "bounceOut")
        )
        
        self.status_text = ft.Text("SYSTEM ONLINE", color="cyan100", size=16, weight="bold")

        # Assemble Layout
        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Container(height=20), # Spacer
                    self.reactor_outer,
                    ft.Container(height=10),
                    self.status_text,
                    ft.Divider(color="cyan900"),
                    self.chat_list
                ], horizontal_alignment="center"),
                expand=True,
                padding=20
            )
        )
        
        # Start background task to listen to events
        self.page.run_task(self.event_listener)
        
        # Drag and Drop Handler
        self.page.on_file_drop = self.on_file_drop
        self.page.update()

    async def on_file_drop(self, e):
        """Handle file drop."""
        # e.files is list of FileDropEventFile
        import structlog
        logger = structlog.get_logger()
        logger.info(f"File Drop Detected: {e.files}")
        
        if not e.files:
            return
            
        file_path = e.files[0].path
        
        self.status_text.value = f"ABSORBING: {e.files[0].name}"
        self.page.update()
        
        # Publish to VoiceManager
        await internal_bus.publish("analyze_file", {"path": file_path})

    async def event_listener(self):
        """Poll specific events or subscribe."""
        # Subscribe to internal_bus events
        internal_bus.subscribe("user_message", self.on_user_message)
        internal_bus.subscribe("assistant_message", self.on_assistant_message)
        internal_bus.subscribe("status_update", self.on_status_update)
        
        # Keep alive
        while True:
            await asyncio.sleep(1)

    async def on_user_message(self, data):
        self.add_chat_bubble(data.get("text", ""), is_user=True)
        
    async def on_assistant_message(self, data):
        self.add_chat_bubble(data.get("text", ""), is_user=False)
        
    async def on_status_update(self, data):
        status = data.get("status", "")
        self.status_text.value = status.upper()
        
        # Simple animation states
        if status == "listening":
            self.reactor_core.bgcolor = "red400"
            self.reactor_core.shadow.color = "red200"
            self.reactor_outer.scale = 1.1
        elif status == "speaking":
            self.reactor_core.bgcolor = "green400"
            self.reactor_core.shadow.color = "green200"
            self.reactor_outer.scale = 1.1
        elif status == "thinking":
            self.reactor_core.bgcolor = "yellow400"
            self.reactor_core.shadow.color = "yellow200"
            self.reactor_outer.scale = 0.9
        else: # Idle
            self.reactor_core.bgcolor = "cyan400"
            self.reactor_core.shadow.color = "cyan200"
            self.reactor_outer.scale = 1.0
            
        self.page.update()

    def add_chat_bubble(self, text, is_user):
        bubble_color = "blueGrey900" if is_user else "cyan900"
        alignment = "end" if is_user else "start"
        
        self.chat_list.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(text, color="white"),
                        bgcolor=bubble_color,
                        padding=10,
                        border_radius=10,
                        width=300 # Limit width
                    )
                ],
                alignment=alignment
            )
        )
        self.page.update()
