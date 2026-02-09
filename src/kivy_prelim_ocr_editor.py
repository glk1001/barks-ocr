from collections.abc import Callable

import typer
from barks_fantagraphics.comic_book import get_page_str
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.ocr_file_paths import get_ocr_prelim_groups_json_filename
from kivy.config import Config
from kivy.uix.label import Label

# Set the main window size using variables
MAIN_WINDOW_X = 2100
MAIN_WINDOW_Y = 20
MAIN_WINDOW_WIDTH = 2000
MAIN_WINDOW_HEIGHT = 1300

Config.set("graphics", "position", "custom")  # ty:ignore[possibly-missing-attribute]
Config.set("graphics", "left", MAIN_WINDOW_X)  # ty: ignore[possibly-missing-attribute]
Config.set("graphics", "top", MAIN_WINDOW_Y)  # ty: ignore[possibly-missing-attribute]
Config.set("graphics", "width", MAIN_WINDOW_WIDTH)  # ty: ignore[possibly-missing-attribute]
Config.set("graphics", "height", MAIN_WINDOW_HEIGHT)  # ty: ignore[possibly-missing-attribute]

from kivy.app import App  # noqa: E402
from kivy.core.image import Image as CoreImage  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.uix.boxlayout import BoxLayout  # noqa: E402
from kivy.uix.button import Button  # noqa: E402
from kivy.uix.image import Image  # noqa: E402
from kivy.uix.popup import Popup  # noqa: E402
from kivy.uix.textinput import TextInput  # noqa: E402
from kivy.uix.widget import Widget  # noqa: E402


def edit_panel_text(
    text_to_edit: str, image: str, on_save_callback: Callable[[str], None]
) -> Popup:
    """Open a popup to edit text alongside an image.

    Args:
        text_to_edit: The initial string to display in the text box.
        image: The file path to the image to display.
        on_save_callback: A function that accepts a string. This is called
                          with the edited text when the user clicks 'Save'.

    Returns:
        The Popup instance (already opened).
    """
    # 0. Calculate Image Aspect Ratio
    cim = CoreImage(image)
    img_ratio = cim.height / cim.width

    # 1. Create the main layout for the popup (Vertical)
    content_layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

    # 2. Create the editor area (Horizontal: Text | Image)
    editor_area = BoxLayout(orientation="horizontal", spacing=10)

    # Text Input (Left side)
    text_input = TextInput(
        text=text_to_edit,
        multiline=True,
        size_hint_x=0.5,  # Take up 50% width
        hint_text="Edit text here...",
    )

    # Image (Right side)
    # If image path is invalid, Kivy displays a placeholder pattern automatically.
    img_widget = Image(
        texture=cim.texture,
        size_hint_x=0.5,  # Take up 50% width
        allow_stretch=True,
        keep_ratio=True,
    )

    editor_area.add_widget(text_input)
    editor_area.add_widget(img_widget)

    # 3. Create the Save button
    save_btn = Button(text="Save & Close", size_hint_y=None, height=50)

    # Add widgets to content layout
    content_layout.add_widget(editor_area)
    content_layout.add_widget(save_btn)

    # 4. Create the Popup
    popup = Popup(
        title="Edit Panel Text",
        content=content_layout,
        size_hint=(0.9, None),
        auto_dismiss=False,
    )

    def update_height(_instance: Popup, _width: float) -> None:
        # Image takes approx 50% of width.
        target_img_h = (popup.width * 0.5) * img_ratio
        # Add space for button (50), spacing (10), padding (20), title bar (~70)
        extra_ui_height = 150
        calculated_height = target_img_h + extra_ui_height
        # Clamp to screen height
        popup.height = min(calculated_height, Window.height * 0.95)

    popup.bind(width=update_height)

    # 5. Define the save action
    def on_save(_instance: Button) -> None:
        edited_text = text_input.text
        popup.dismiss()
        if on_save_callback:
            on_save_callback(edited_text)

    save_btn.bind(on_press=on_save)

    popup.open()
    return popup


class EditorApp(App):
    def __init__(self, volume: int, fanta_page: int, group_id: int) -> None:
        super().__init__()

        self._volume = volume
        self._fanta_page = get_page_str(fanta_page)
        self._group_id = group_id

        self._comics_database = ComicsDatabase()

    def build(self) -> Widget:
        box_layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        ocr_prelim_dir = self._comics_database.get_fantagraphics_restored_ocr_prelim_volume_dir(
            self._volume
        )
        easy_ocr_file = ocr_prelim_dir / get_ocr_prelim_groups_json_filename(
            self._fanta_page, "easyocr"
        )
        paddle_ocr_file = ocr_prelim_dir / get_ocr_prelim_groups_json_filename(
            self._fanta_page, "paddleocr"
        )
        easy_ocr_file_label = Label(text=str(easy_ocr_file))
        paddle_ocr_file_label = Label(text=str(paddle_ocr_file))
        # Main button to trigger the editor
        btn = Button(text="Click to Edit Panel")
        btn.bind(on_press=self.trigger_edit)

        box_layout.add_widget(easy_ocr_file_label)
        box_layout.add_widget(paddle_ocr_file_label)
        box_layout.add_widget(btn)

        return box_layout

    def trigger_edit(self, _instance: Button) -> None:
        # Example usage:
        # We pass a lambda or method to handle the returned text.
        edit_panel_text(
            text_to_edit="Original text content goes here.",
            image="/home/greg/Books/Carl Barks/Barks Panels Pngs/Insets/All at Sea.png",  # Replace with a valid path on your system
            on_save_callback=self.handle_result,
        )

    def handle_result(self, new_text: str) -> None:
        print(f"User finished editing. New text:\n{new_text}")


app = typer.Typer()


@app.command(help="Prelim OCR Text Editor")
def main(
    volume: int,
    fanta_page: int,
    group_id: int,
) -> None:
    EditorApp(volume, fanta_page, group_id).run()


if __name__ == "__main__":
    app()
