import os
from collections.abc import Callable

from kivy.app import App
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget


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
    """Example Application to demonstrate the function."""

    def build(self) -> Widget:
        # Main button to trigger the editor
        btn = Button(text="Click to Edit Panel")
        btn.bind(on_press=self.trigger_edit)
        return btn

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


if __name__ == "__main__":
    # Set the main window size using variables
    MAIN_WINDOW_WIDTH = 1200
    MAIN_WINDOW_HEIGHT = 900
    Window.size = (MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)
    EditorApp().run()
