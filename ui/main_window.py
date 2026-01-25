import flet as ft
import asyncio
import math
from core.event_bus import internal_bus
from core.config import global_settings

class JarvisUI:
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
        
        # Arc Reactor - Iron Man Style with multiple concentric rings
        # Inner core (brightest)
        self.reactor_core = ft.Container(
            width=40,
            height=40,
            bgcolor="#00D9FF",
            border_radius=20,
            alignment=ft.Alignment(0, 0),
            shadow=ft.BoxShadow(
                spread_radius=15, 
                blur_radius=30, 
                color="#00D9FF"
            ),
            animate=ft.Animation(500, "easeInOut"),
        )
        
        # First ring
        self.ring_1 = ft.Container(
            width=80,
            height=80,
            border=ft.border.all(3, "#00A8CC"),
            border_radius=40,
            bgcolor="transparent",
            content=self.reactor_core,
            alignment=ft.Alignment(0, 0),
        )
        
        # Second ring with segments
        self.ring_2 = ft.Container(
            width=110,
            height=110,
            border=ft.border.all(2, "#008BA3"),
            border_radius=55,
            bgcolor="transparent",
            content=self.ring_1,
            alignment=ft.Alignment(0, 0),
        )
        
        # Third ring
        self.ring_3 = ft.Container(
            width=140,
            height=140,
            border=ft.border.all(2, "#00667A"),
            border_radius=70,
            bgcolor="transparent",
            content=self.ring_2,
            alignment=ft.Alignment(0, 0),
        )
        
        # Outer housing with metallic look
        self.reactor_housing = ft.Container(
            width=180,
            height=180,
            border=ft.border.all(4, "#2C3E50"),
            border_radius=90,
            bgcolor="#0A1929",
            content=self.ring_3,
            alignment=ft.Alignment(0, 0),
            shadow=ft.BoxShadow(
                spread_radius=5, 
                blur_radius=15, 
                color="#00D9FF30"
            ),
            animate_scale=ft.Animation(500, "bounceOut")
        )
        
        # Container with radial gradient effect simulation
        self.reactor_outer = ft.Stack(
            [
                # Background glow
                ft.Container(
                    width=200,
                    height=200,
                    border_radius=100,
                    bgcolor="#00334D20",
                ),
                # Main reactor
                ft.Container(
                    width=200,
                    height=200,
                    content=self.reactor_housing,
                    alignment=ft.Alignment(0, 0),
                ),
            ],
            width=200,
            height=200,
        )
        
        self.status_text = ft.Text(
            "SYSTEM ONLINE", 
            color="#00D9FF", 
            size=16, 
            weight="bold",
            text_align="center"
        )

        # Assemble Layout
        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Container(height=20), # Spacer
                    ft.Container(
                        content=self.reactor_outer,
                        alignment=ft.Alignment(0, 0)
                    ),
                    ft.Container(height=10),
                    self.status_text,
                    ft.Divider(color="#00667A"),
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
        
        # Arc Reactor color states like Iron Man
        if status == "listening":
            # Red alert mode
            self.reactor_core.bgcolor = "#FF3333"
            self.reactor_core.shadow.color = "#FF3333"
            self.ring_1.border = ft.border.all(3, "#CC0000")
            self.ring_2.border = ft.border.all(2, "#990000")
            self.ring_3.border = ft.border.all(2, "#660000")
            self.reactor_housing.shadow.color = "#FF333330"
            self.reactor_housing.scale = 1.1
            self.status_text.color = "#FF3333"
            
        elif status == "speaking":
            # Green active mode
            self.reactor_core.bgcolor = "#00FF88"
            self.reactor_core.shadow.color = "#00FF88"
            self.ring_1.border = ft.border.all(3, "#00CC66")
            self.ring_2.border = ft.border.all(2, "#009944")
            self.ring_3.border = ft.border.all(2, "#006622")
            self.reactor_housing.shadow.color = "#00FF8830"
            self.reactor_housing.scale = 1.1
            self.status_text.color = "#00FF88"
            
        elif status == "thinking":
            # Yellow processing mode
            self.reactor_core.bgcolor = "#FFD700"
            self.reactor_core.shadow.color = "#FFD700"
            self.ring_1.border = ft.border.all(3, "#CCAA00")
            self.ring_2.border = ft.border.all(2, "#997700")
            self.ring_3.border = ft.border.all(2, "#665500")
            self.reactor_housing.shadow.color = "#FFD70030"
            self.reactor_housing.scale = 0.95
            self.status_text.color = "#FFD700"
            
        else: # Idle - Classic Arc Reactor blue
            self.reactor_core.bgcolor = "#00D9FF"
            self.reactor_core.shadow.color = "#00D9FF"
            self.ring_1.border = ft.border.all(3, "#00A8CC")
            self.ring_2.border = ft.border.all(2, "#008BA3")
            self.ring_3.border = ft.border.all(2, "#00667A")
            self.reactor_housing.shadow.color = "#00D9FF30"
            self.reactor_housing.scale = 1.0
            self.status_text.color = "#00D9FF"
            
        self.page.update()

    def add_chat_bubble(self, text, is_user):
        bubble_color = "#1E3A5F" if is_user else "#0A3D4D"
        alignment = "end" if is_user else "start"
        text_color = "#E0E0E0" if is_user else "#00D9FF"
        
        self.chat_list.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(text, color=text_color),
                        bgcolor=bubble_color,
                        padding=10,
                        border_radius=10,
                        border=ft.border.all(1, "#00667A40"),
                        width=300 # Limit width
                    )
                ],
                alignment=alignment
            )
        )
        self.page.update()