from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.screen import Screen
from textual.widgets import LoadingIndicator
from textual.widgets import Label
from textual.app import App
from textual import work
from asyncio import sleep
from textual.binding import Binding
from textual.widgets import Footer
from asyncio import run
import asyncio
import time


class Loading(ModalScreen):
    def compose(self) -> ComposeResult:
        yield LoadingIndicator()

    @work(exclusive=True)
    async def wait(self):
        await asyncio.get_event_loop().run_in_executor(None, time.sleep, 3)
        self.dismiss()

    def on_mount(self) -> None:
        self.wait()


class Index(Screen):
    BINDINGS = [
        Binding(key="d", action="demo", description="deal"),
    ]

    def compose(self) -> ComposeResult:
        yield Label("index")
        yield Footer()


class APP(App):

    def on_mount(self) -> None:
        self.install_screen(Index(), "index")
        self.push_screen("index")

    async def action_demo(self):
        await self.push_screen(Loading())


async def main():
    await APP().run_async()


if __name__ == "__main__":
    run(main())