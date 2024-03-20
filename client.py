from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Input, Label, Button, Static, LoadingIndicator, Header, Footer, TextArea
from textual.screen import Screen
import asyncio
import time
import threading
import sys
import os

from core import client_func

def StartConnection(host: str, port: int, nickname: str):
    time.sleep(5)
    try:
        if host.endswith(".onion"):
            tor = True
        else:
            tor = False
        client = client_func.Client(host=host, port=port, tor=tor, nickname=nickname)
        
        res = client.connect()
        if res:
            return client
        else:
            return False
    except Exception as e:
        return False
    
def recv_thread(client: client_func.Client, output: TextArea):
    while True:
        data = client.recv_encrypt(client.client_sock, privkey=client.PRIVATE_KEY)
        output.text += data.decode() + "\n" 
        output.scroll_end(animate=False)
 
class Join(Static):
    def compose(self):
        yield Label("Join Server", id="join_label", expand=True)
        yield Input(placeholder="Host", id="host_input")
        yield Input(placeholder="Port", id="port_input", type="integer")
        yield Input(placeholder="Nickname", id="nickname_input")
        yield Button("Join", id="join_button")


class ChatApp(Screen):
    def __init__(self, host, port, client: client_func.Client, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        self.host = host
        self.port = port
        self.client = client
        super().__init__(name, id, classes)

    def compose(self):
        yield Header(show_clock="True")
        Header.screen_title = f"{self.host}:{str(self.port)}"

        yield Footer()

        self.output_text_area = TextArea("", read_only=True, id="chat_output")
        yield self.output_text_area

        yield Input("", placeholder="Enter Message", id="chat_input")
        
    def on_mount(self):
        threading.Thread(target=recv_thread, args=(self.client, self.output_text_area)).start()

class Connect(Screen):
    def __init__(self, host, port, nickname, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        self.host = host
        self.port = port
        self.nickname = nickname
        super().__init__(name, id, classes)

    def compose(self) -> ComposeResult:
        yield LoadingIndicator()

    @work(exclusive=True)
    async def connect(self):
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, StartConnection, self.host, self.port, self.nickname)
        self.dismiss(res)

    def on_mount(self) -> None:
        self.connect()

class ClientApp(App[str]):
    ENABLE_COMMAND_PALETTE = False
    CSS_PATH = "css/client.tcss"

    def compose(self):
        yield Join()

    async def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == "join_button":
            JoinForm = self.query_one(Join)
            host = JoinForm.get_child_by_id("host_input")
            port = JoinForm.get_child_by_id("port_input")
            nickname = JoinForm.get_child_by_id("nickname_input")

            def check_join(join):
                if join != False and type(join) == client_func.Client:
                    self.notify("Connected to Server")
                    self.push_screen(ChatApp(host=host.value, port=int(port.value), client=join))
                else:
                    self.notify("Error Connecting To Server", severity="error")
            
            if nickname.value == "" or nickname.value == None:
                nickname.value = "AnonymousUser"
            
            self.push_screen(Connect(host=host.value, port=int(port.value), nickname=nickname.value), check_join)

    async def on_input_submitted(self, event: Input.Submitted):
        input_id = event.input.id
        if input_id == "chat_input":
            chatapp = self.query_one(ChatApp)
            client = chatapp.client
            client.send_encrypt(socket_obj=client.client_sock, data=event.value.encode(), pubkey=client.SERVER_PUBLIC_KEY)
            event.input.clear()

if __name__ == "__main__":
    ClientApp().run()