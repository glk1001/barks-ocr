import json
from collections.abc import Callable
from pathlib import Path

import typer
from barks_fantagraphics.comic_book import get_page_str
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_utils import get_abbrev_path
from barks_fantagraphics.ocr_file_paths import get_ocr_prelim_groups_json_filename
from comic_utils.comic_consts import PNG_FILE_EXT
from comic_utils.pil_image_utils import load_pil_image_for_reading
from kivy.config import Config

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
from kivy.uix.boxlayout import BoxLayout  # noqa: E402
from kivy.uix.button import Button  # noqa: E402
from kivy.uix.image import Image  # noqa: E402
from kivy.uix.label import Label  # noqa: E402
from kivy.uix.textinput import TextInput  # noqa: E402
from kivy.uix.widget import Widget  # noqa: E402


# TODO: Duplicated in 'edit-page.py'.
def write_cropped_image_file(
    srce_image_file: Path, segments_file: Path, target_image_file: Path, panel: int
) -> None:
    if panel <= 0 or panel >= 9:
        msg = f'Srce image file: "{srce_image_file}" - invalid panel number "{panel}".'
        raise ValueError(msg)

    if not segments_file.is_file():
        print(f'WARN: Could not find segments file "{segments_file}". Returning full page.')
        image = load_pil_image_for_reading(srce_image_file)
        image.save(target_image_file, optimize=True, compress_level=9)
    else:
        with segments_file.open() as f:
            panel_segment_info = json.load(f)

        if panel <= 0 or panel > len(panel_segment_info["panels"]):
            msg = f'Segments file: "{segments_file}" - invalid panel number "{panel}".'
            raise ValueError(msg)

        panel_box = panel_segment_info["panels"][panel - 1]

        left = panel_box[0]
        bottom = panel_box[1]
        right = left + panel_box[2]
        upper = bottom + panel_box[3]

        image = load_pil_image_for_reading(srce_image_file)
        subimage = image.crop((left, bottom, right, upper))
        subimage.save(target_image_file, optimize=True, compress_level=5)


def _encode_for_display(text: str) -> str:
    return text.encode("unicode_escape").decode("utf-8").replace(r"\n", "\n")


def _decode_from_display(text: str) -> str:
    return text.replace("\n", r"\n").encode("utf-8").decode("unicode_escape")


def create_editor_widget(
    text_to_edit_1: str,
    edit_label1: str,
    text_to_edit_2: str,
    edit_label2: str,
    image: Path,
    extra_info: str,
    on_save_callback: Callable[[str, str], None],
) -> BoxLayout:
    """Create a widget to edit text alongside an image.

    Args:
        text_to_edit_1: The first initial string to display (top).
        edit_label1: Label text for the first text box.
        text_to_edit_2: The second initial string to display (bottom).
        edit_label2: Label text for the second text box.
        image: The file path to the image to display.
        extra_info: Text to display in a label under the image.
        on_save_callback: A function that accepts two strings. This is called
                          with the edited texts when the user clicks 'Save'.

    Returns:
        The BoxLayout containing the editor.
    """
    # 0. Calculate Image Aspect Ratio
    cim = CoreImage(str(image))

    # 1. Create the main layout for the popup (Vertical)
    content_layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

    # 2. Create the editor area (Horizontal: Text | Image)
    editor_area = BoxLayout(orientation="horizontal", spacing=10)

    # Text Inputs (Left side - Vertical Layout)
    text_layout = BoxLayout(orientation="vertical", spacing=10, size_hint_x=0.5)

    label_1 = Label(text=edit_label1, size_hint_y=None, height=30)
    text_input_1 = TextInput(
        text=_encode_for_display(text_to_edit_1),
        font_size="20sp",
        multiline=True,
        size_hint_y=1,
        padding=10,
        hint_text="Edit text 1 here...",
    )
    label_2 = Label(text=edit_label2, size_hint_y=None, height=30)
    text_input_2 = TextInput(
        text=_encode_for_display(text_to_edit_2),
        font_size="20sp",
        multiline=True,
        size_hint_y=1,
        padding=10,
        hint_text="Edit text 2 here...",
    )
    text_layout.add_widget(label_1)
    text_layout.add_widget(text_input_1)
    text_layout.add_widget(label_2)
    text_layout.add_widget(text_input_2)

    # Right side (Image + Extra Info)
    right_layout = BoxLayout(orientation="vertical", size_hint_x=0.5)

    img_widget = Image(
        texture=cim.texture,
        size_hint_y=0.8,
        allow_stretch=True,
        keep_ratio=True,
    )
    info_label = Label(
        text=extra_info, size_hint_y=0.2, font_size="15sp", halign="left", valign="top"
    )
    info_label.bind(size=info_label.setter("text_size"))

    right_layout.add_widget(img_widget)
    right_layout.add_widget(info_label)

    editor_area.add_widget(text_layout)
    editor_area.add_widget(right_layout)

    # 3. Create the Save button
    save_btn = Button(text="Save & Exit", size_hint_y=None, height=50)

    # Add widgets to content layout
    content_layout.add_widget(editor_area)
    content_layout.add_widget(save_btn)

    # 5. Define the save action
    def on_save(_instance: Button) -> None:
        try:
            edited_text_1 = _decode_from_display(text_input_1.text)
            edited_text_2 = _decode_from_display(text_input_2.text)
        except UnicodeDecodeError as e:
            print(f"Error decoding text: {e}")
            return

        if on_save_callback:
            on_save_callback(edited_text_1, edited_text_2)
        App.get_running_app().stop()

    save_btn.bind(on_press=on_save)

    return content_layout


class EditorApp(App):
    def __init__(self, volume: int, fanta_page: int, group_id: int, panel_num: int) -> None:
        super().__init__()

        self._volume = volume
        self._fanta_page = get_page_str(fanta_page)
        self._group_id = str(group_id)
        self._panel_num = panel_num

        self._comics_database = ComicsDatabase()

        restored_images_dir = self._comics_database.get_fantagraphics_restored_volume_image_dir(
            self._volume
        )
        self._srce_image_file = restored_images_dir / (self._fanta_page + PNG_FILE_EXT)

        ocr_prelim_dir = self._comics_database.get_fantagraphics_restored_ocr_prelim_volume_dir(
            self._volume
        )
        self._easyocr_file = ocr_prelim_dir / get_ocr_prelim_groups_json_filename(
            self._fanta_page, "easyocr"
        )
        self._paddleocr_file = ocr_prelim_dir / get_ocr_prelim_groups_json_filename(
            self._fanta_page, "paddleocr"
        )

        self._easyocr_text = get_ai_text(self._easyocr_file, self._group_id)
        self._paddleocr_text = get_ai_text(self._paddleocr_file, self._group_id)

        panel_segments_dir = Path(
            self._comics_database.get_fantagraphics_panel_segments_volume_dir(self._volume)
        )
        self._panel_segments_file = panel_segments_dir / (self._fanta_page + ".json")

    def _get_editor_info(self) -> str:
        return (
            f"Volume: {self._volume}\n"
            f"Fanta Page: {self._fanta_page}\n"
            f"Group ID: {self._group_id}\n"
            f"Panel: {self._panel_num}\n"
            f'EasyOCR file: {get_abbrev_path(self._easyocr_file)}"\n'
            f'PaddleOCR file: {get_abbrev_path(self._paddleocr_file)}"\n'
            f'Image file: {get_abbrev_path(self._srce_image_file)}"\n'
            f'Segments file: {get_abbrev_path(self._panel_segments_file)}"\n'
        )

    def build(self) -> Widget:
        return create_editor_widget(
            text_to_edit_1=self._easyocr_text,
            edit_label1="EasyOCR",
            text_to_edit_2=self._paddleocr_text,
            edit_label2="PaddleOCR",
            image=self.get_panel_image_file(),
            extra_info=self._get_editor_info(),
            on_save_callback=self.handle_result,
        )

    def get_panel_image_file(self) -> Path:
        panel_image_file = Path("/tmp") / (f"{self._volume}-{self._fanta_page}" + PNG_FILE_EXT)
        write_cropped_image_file(
            self._srce_image_file, self._panel_segments_file, panel_image_file, self._panel_num
        )
        return panel_image_file

    def handle_result(self, new_easyocr_text: str, new_paddleocr_text: str) -> None:
        if self._easyocr_text != new_easyocr_text:
            save_ai_text(self._easyocr_file, self._group_id, new_easyocr_text)
            print(
                f'Saved new easyocr text to file "{self._easyocr_file}". Text:\n{new_easyocr_text}'
            )
        if self._paddleocr_text != new_paddleocr_text:
            save_ai_text(self._paddleocr_file, self._group_id, new_paddleocr_text)
            print(
                f'Saved new paddleocr text to file "{self._paddleocr_file}".'
                f" Text:\n{new_paddleocr_text}"
            )


def get_ai_text(ocr_file: Path, group_id: str) -> str:
    ocr_page = json.loads(ocr_file.read_text())
    if group_id not in ocr_page["groups"]:
        return ""
    # if group_id not in ocr_page["groups"]:
    #     msg = f"Could not find group id '{group_id}' in OCR file '{ocr_file}'."
    #     raise RuntimeError(msg)
    return ocr_page["groups"][group_id]["ai_text"]


def save_ai_text(ocr_file: Path, group_id: str, text: str) -> None:
    ocr_page = json.loads(ocr_file.read_text())
    if group_id not in ocr_page["groups"]:
        msg = f"Could not find group id '{group_id}' in OCR file '{ocr_file}'."
        raise RuntimeError(msg)
    ocr_page["groups"][group_id]["ai_text"] = text

    tmp_ocr_file = Path("/tmp") / ocr_file.name

    with tmp_ocr_file.open("w") as f:
        json.dump(ocr_page, f, indent=4)


app = typer.Typer()


@app.command(help="Prelim OCR Text Editor")
def main(
    volume: int,
    fanta_page: int,
    group_id: int,
    panel_num: int,
) -> None:
    EditorApp(volume, fanta_page, group_id, panel_num).run()


if __name__ == "__main__":
    app()
