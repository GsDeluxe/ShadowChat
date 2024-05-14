
from textual import work, on
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TextArea, Input, LoadingIndicator, Static, Label, Button
from textual.screen import Screen
import asyncio
import threading

import os
from core import server_func

import time

def StartServer(host, port, tor):
    time.sleep(1)
    try:
        server = server_func.Server(host=host, port=port, tor=tor)
        res = server.create_socket()
        if res:
            return server
        else:
            return False
    except:
        return False
    
def chat_thread(server: server_func.Server, output_box: TextArea):
    last_msg = ""
    while True:
        last_msg = server.last_msg
        if last_msg:
            output_box.text += last_msg + "\n"
            server.last_msg = None
            output_box.scroll_end(animate=False)
        time.sleep(0.1)

class BuildServer(Screen):
    def __init__(self, host, port, tor, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        self.host = host
        self.port = port
        self.tor = tor
        super().__init__(name, id, classes)

    def compose(self):
        yield LoadingIndicator()

    @work(exclusive=True)
    async def build_server(self):
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, StartServer, self.host, self.port, self.tor)
        self.dismiss(res)

    def on_mount(self):
        self.build_server()

class ServerConsole(Screen):
    def __init__(self, host, port, server: server_func.Server, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        self.host = host
        self.port = port
        self.server = server
        super().__init__(name=name, id=id, classes=classes)
    
    def compose(self):
        yield Header(show_clock="True")
        yield Footer()

        self.output_text_area = TextArea("", read_only=True, id="chat_output")
        yield self.output_text_area


        yield Input("", placeholder="[SERVER] Enter Message", id="chat_input")
    
    def on_mount(self):
        if self.server.tor:
            self.host = self.server.hostname
        
        self.output_text_area.text += f"[+] Server Online: {self.host}:{str(self.port)}" + "\n"

        threading.Thread(target=chat_thread, args=(self.server, self.output_text_area, ), daemon=True).start()

class YesNo(Screen[bool]):

    def __init__(self, question: str) -> None:
        self.question = question
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Label(self.question)
        yield Button("Yes", id="yes")
        yield Button("No", id="no")

    @on(Button.Pressed, "#yes")
    def handle_yes(self) -> None:
        self.dismiss(True)  

    @on(Button.Pressed, "#no")
    def handle_no(self) -> None:
        self.dismiss(False)

class ServerInfo(Static):

    def compose(self):
        yield Label("Start Server", id="start_label", expand=True)
        yield Input(placeholder="Host", id="host_input")
        yield Input(placeholder="Port", id="port_input", type="integer")
        yield Button("Start Server", id="start_button")

class ServerApp(App[str]):
    CSS_PATH = "css/server.tcss"
    ENABLE_COMMAND_PALETTE = False

    def compose(self):
        yield ServerInfo()

    async def on_input_submitted(self, event: Input.Submitted):
        input_id = event.input.id
        if input_id == "chat_input":
            serverconsole = self.query_one(ServerConsole)
            server = serverconsole.server
            server.broadcast_msg(event.value.encode(), nickname=b"Server")
            event.input.clear()

    @work
    async def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == "start_button":
            ServerForm = self.query_one(ServerInfo)
            host = ServerForm.get_child_by_id("host_input")
            port = ServerForm.get_child_by_id("port_input")

            if host.value == None or host.value == "" or port.value == "" or port.value == None:
                self.notify("Error Missing Values", severity="error")
                return

            if await self.push_screen_wait(YesNo(question="Use TOR?")):
                tor = True
            else:
                tor = False
            

            def server_start_handle(res):
                if res != False and type(res) == server_func.Server:
                    self.notify("Created Server")
                    self.push_screen(ServerConsole(host=host.value, port=int(port.value), server=res))
                else:
                    self.notify("Error Creating Server", severity="error")

            await self.push_screen(BuildServer(host=host.value, port=int(port.value), tor=tor), server_start_handle)
            

ServerApp().run()