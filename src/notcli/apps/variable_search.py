import os
import subprocess

from rich.console import RenderableType
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import (
    Input,
    Static,
    Label,
    RadioSet,
    RadioButton,
    Header,
    Footer,
    TextLog,
)
import asyncio

from src.notcli.conf.settings import STATIC_DIR, TTY_ECHO_PATH


class Column(Container):
    pass


class VariableDialog(ModalScreen):
    def __init__(self, variable: str, **kwargs):
        super().__init__(**kwargs)
        self.variable = variable

    def compose(self) -> ComposeResult:
        yield Container(
            Header(show_clock=False),
            Column(
                Label(f"Variable: {self.variable}", id="variable_label"),
                RadioSet(
                    RadioButton("Override", id="override", value=True),
                    RadioButton("Append", id="append", value=False),
                ),
            ),
        )
        yield Footer()

    def on_radio_button_changed(self, event: RadioButton.Changed) -> None:
        if event.radio_button.value == "override":
            self.app.override_variable(self.variable)
        elif event.radio_button.value == "append":
            self.app.append_to_variable(self.variable)
        self.app.pop_screen()


class VariableSearchApp(App):
    BINDINGS = [
        ("f1", "app.toggle_class('TextLog', '-hidden')", "Notes"),
    ]
    CSS_PATH = f"{STATIC_DIR}/variable_search.css"
    variables = os.environ.copy()

    def compose(self) -> ComposeResult:
        yield Container(
            Header(show_clock=False),
            TextLog(wrap=False, highlight=True, markup=True),
            Input(placeholder="Search for a variable", id="variable_input"),
            Static(id="results"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self.app.add_note(
            "This app will search for a variable in the environment and display the results."
        )
        self.query_one(Input).focus()

    def add_note(self, renderable: RenderableType) -> None:
        self.query_one(TextLog).write(renderable)

    async def on_input_changed(self, message: Input.Changed) -> None:
        """A coroutine to handle a text changed message."""
        if message.value:
            # Search for the variable in the background
            asyncio.create_task(self.lookup_variable(message.value))
        else:
            # Clear the results
            self.query_one("#results", Static).update()

    async def lookup_variable(self, variable: str) -> None:
        """Looks up a variable."""
        result = self.variables.get(variable, "Variable not found")
        if variable == self.query_one("#variable_input", Input).value:
            self.query_one("#results", Static).update(result)
        if result != "Variable not found":
            # Open the dialog to ask if the user wants to override or append
            self.open_dialog(variable)

    def open_dialog(self, variable: str) -> None:
        """Open a dialog with options to override or append to the variable."""
        dialog = VariableDialog(variable)
        self.push_screen(dialog)

    @staticmethod
    def get_tty():
        try:
            result = subprocess.run(
                ["tty"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            result.check_returncode()
            return result.stdout.decode().strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to get current terminal: {e.stderr.decode().strip()}"
            )

    def override_variable(self, variable: str) -> None:
        self.add_note(f"Override {variable}")
        """Override the selected variable."""
        # Here you could get the new value from another Input widget or from a user prompt
        new_value = self.get_new_value(variable)  # You need to define this function
        self.variables[variable] = new_value
        tty = self.get_tty()
        command_str = "echo test"
        sleep_and_run = f"sleep 0.3 && {TTY_ECHO_PATH}/ttyecho -n {tty} '{command_str}'"
        subprocess.Popen(sleep_and_run, shell=True)
        self.app.exit()

    def append_to_variable(self, variable: str) -> None:
        self.add_note(f"Append to {variable}")
        self.app.exit()
        """Append to the selected variable."""
        # Here you could get the value to append from another Input widget or from a user prompt
        value_to_append = self.get_value_to_append(
            variable
        )  # You need to define this function
        self.variables[variable] += value_to_append

    def get_value_to_append(self, variable):
        print(variable)
        return "test"

    def get_new_value(self, variable):
        print(variable)
        return "test"


if __name__ == "__main__":
    app = VariableSearchApp()
    app.run()
