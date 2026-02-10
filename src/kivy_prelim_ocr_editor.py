import json
from collections.abc import Callable
from pathlib import Path

import typer
from barks_fantagraphics.barks_titles import BARKS_TITLE_DICT, BARKS_TITLES
from barks_fantagraphics.comic_book import get_page_str
from barks_fantagraphics.comics_consts import FONT_DIR, OPEN_SANS_FONT
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_title_from_volume_page
from barks_fantagraphics.comics_utils import get_abbrev_path
from barks_fantagraphics.speech_groupers import get_speech_page_group_with_json
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
from kivy.core.text import LabelBase  # noqa: E402
from kivy.uix.boxlayout import BoxLayout  # noqa: E402
from kivy.uix.button import Button  # noqa: E402
from kivy.uix.checkbox import CheckBox  # noqa: E402
from kivy.uix.image import Image  # noqa: E402
from kivy.uix.label import Label  # noqa: E402
from kivy.uix.textinput import TextInput  # noqa: E402
from kivy.uix.widget import Widget  # noqa: E402

# TODO: Duplicated in 'font_manager.py'.
# Set up custom fonts.
LabelBase.register(
    name=OPEN_SANS_FONT,
    fn_regular=str(FONT_DIR / "OpenSans-Medium.ttf"),
    fn_bold=str(FONT_DIR / "OpenSans-Bold.ttf"),
    fn_italic=str(FONT_DIR / "OpenSans-MediumItalic.ttf"),
    fn_bolditalic=str(FONT_DIR / "OpenSans-BoldItalic.ttf"),
)


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
        font_name=OPEN_SANS_FONT,
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
        font_name=OPEN_SANS_FONT,
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

    right_layout.add_widget(Widget(size_hint_y=None, height=35))

    # Checkbox for Unicode decoding
    checkbox_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=30)
    decode_checkbox = CheckBox(active=True, size_hint_x=None, width=30)
    decode_label = Label(text="Show Unicode", halign="left", valign="middle")
    decode_label.bind(size=decode_label.setter("text_size"))
    checkbox_layout.add_widget(decode_checkbox)
    checkbox_layout.add_widget(decode_label)
    right_layout.add_widget(checkbox_layout)

    img_widget = Image(
        texture=cim.texture,
        size_hint_y=0.8,
        allow_stretch=True,
        keep_ratio=True,
    )
    info_label = Label(
        text=extra_info,
        size_hint_y=0.2,
        font_size="17sp",
        halign="left",
        valign="top",
        padding=10,
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

    def update_diff_labels(*_args) -> None:  # noqa: ANN002
        try:
            t1 = text_input_1.text
            t2 = text_input_2.text
            if decode_checkbox.active:  # If True, text is encoded for display
                t1 = _decode_from_display(t1)
                t2 = _decode_from_display(t2)

            are_different = t1 != t2

            if are_different:
                label_1.text = f"{edit_label1}  -- DIFFS"
                label_2.text = f"{edit_label2}  -- DIFFS"
                label_1.color = (1, 0, 0, 1)  # Red
                label_2.color = (1, 0, 0, 1)  # Red
            else:
                label_1.text = edit_label1
                label_2.text = edit_label2
                label_1.color = (1, 1, 1, 1)  # Default/White
                label_2.color = (1, 1, 1, 1)  # Default/White
        except UnicodeDecodeError:
            # During typing, an invalid escape sequence might exist temporarily.
            # We can just ignore the update in this case.
            pass

    text_input_1.bind(text=update_diff_labels)
    text_input_2.bind(text=update_diff_labels)

    def on_checkbox_active(_instance: CheckBox, value: bool) -> None:
        try:
            t1 = text_input_1.text
            t2 = text_input_2.text
            if value:
                # Decoded -> Encoded
                text_input_1.text = _encode_for_display(t1)
                text_input_2.text = _encode_for_display(t2)
            else:
                # Encoded -> Decoded
                text_input_1.text = _decode_from_display(t1)
                text_input_2.text = _decode_from_display(t2)
        except UnicodeDecodeError as e:
            print(f"Error converting text: {e}")

    decode_checkbox.bind(active=on_checkbox_active)

    # Set initial state of diff labels
    update_diff_labels()

    # 5. Define the save action
    def on_save(_instance: Button) -> None:
        try:
            if decode_checkbox.active:
                edited_text_1 = _decode_from_display(text_input_1.text)
                edited_text_2 = _decode_from_display(text_input_2.text)
            else:
                edited_text_1 = text_input_1.text
                edited_text_2 = text_input_2.text
        except UnicodeDecodeError as e:
            print(f"Error decoding text: {e}")
            return

        if on_save_callback:
            on_save_callback(edited_text_1, edited_text_2)
        App.get_running_app().stop()

    save_btn.bind(on_press=on_save)

    return content_layout


class EditorApp(App):
    def __init__(
        self,
        volume: int,
        fanta_page: int,
        panel_num: int,
        easyocr_group_id: int,
        paddleocr_group_id: int,
    ) -> None:
        super().__init__()

        self._volume = volume
        self._fanta_page = get_page_str(fanta_page)
        self._panel_num = panel_num
        self._easyocr_group_id = str(easyocr_group_id)
        self._paddleocr_group_id = str(paddleocr_group_id)

        self._comics_database = ComicsDatabase()
        title_str, dest_page = get_title_from_volume_page(
            self._comics_database, volume, self._fanta_page
        )
        self._title = BARKS_TITLE_DICT[title_str]
        self._dest_page = get_page_str(dest_page)

        restored_images_dir = self._comics_database.get_fantagraphics_restored_volume_image_dir(
            self._volume
        )
        self._srce_image_file = restored_images_dir / (self._fanta_page + PNG_FILE_EXT)

        self._easyocr_speech_page_group_with_json = get_speech_page_group_with_json(
            self._comics_database, volume, self._title, 0, self._fanta_page, self._dest_page
        )
        self._paddleocr_speech_page_group_with_json = get_speech_page_group_with_json(
            self._comics_database, volume, self._title, 1, self._fanta_page, self._dest_page
        )

        panel_segments_dir = Path(
            self._comics_database.get_fantagraphics_panel_segments_volume_dir(self._volume)
        )
        self._panel_segments_file = panel_segments_dir / (self._fanta_page + ".json")

    def _get_editor_info(self) -> str:
        easyocr_file = self._easyocr_speech_page_group_with_json.ocr_prelim_groups_json_file
        paddleocr_file = self._paddleocr_speech_page_group_with_json.ocr_prelim_groups_json_file
        return (
            f"Title: {BARKS_TITLES[self._title]}\n"
            f"Volume: {self._volume}\n"
            f"Fanta Page: {self._fanta_page}\n"
            f"Panel: {self._panel_num}\n"
            f"EasyOCR group ID: {self._easyocr_group_id}\n"
            f"PaddleOCR group ID: {self._paddleocr_group_id}\n"
            f'EasyOCR file: {get_abbrev_path(easyocr_file)}"\n'
            f'PaddleOCR file: {get_abbrev_path(paddleocr_file)}"\n'
            f'Image file: {get_abbrev_path(self._srce_image_file)}"\n'
            f'Segments file: {get_abbrev_path(self._panel_segments_file)}"\n'
        )

    def build(self) -> Widget:
        easyocr_text = self._easyocr_speech_page_group_with_json.speech_page_group["speech_groups"][
            self._easyocr_group_id
        ]["raw_ai_text"]
        paddleocr_text = self._paddleocr_speech_page_group_with_json.speech_page_group[
            "speech_groups"
        ][self._paddleocr_group_id]["raw_ai_text"]

        return create_editor_widget(
            text_to_edit_1=easyocr_text,
            edit_label1="EasyOCR",
            text_to_edit_2=paddleocr_text,
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
        easyocr_text = self._easyocr_speech_page_group_with_json.speech_page_group["speech_groups"][
            self._easyocr_group_id
        ]["raw_ai_text"]
        paddleocr_text = self._paddleocr_speech_page_group_with_json.speech_page_group[
            "speech_groups"
        ][self._paddleocr_group_id]["raw_ai_text"]

        if easyocr_text != new_easyocr_text:
            self._easyocr_speech_page_group_with_json.speech_page_group["speech_groups"][
                self._easyocr_group_id
            ]["raw_ai_text"] = new_easyocr_text
            ocr_file = self._easyocr_speech_page_group_with_json.ocr_prelim_groups_json_file
            tmp_ocr_file = Path("/tmp") / ocr_file.name
            self._easyocr_speech_page_group_with_json.save_group(tmp_ocr_file)
            print(f'Saved new easyocr text to file "{tmp_ocr_file}". Text:\n{new_easyocr_text}')
        if paddleocr_text != new_paddleocr_text:
            self._paddleocr_speech_page_group_with_json.speech_page_group["speech_groups"][
                self._paddleocr_group_id
            ]["raw_ai_text"] = new_paddleocr_text
            ocr_file = self._paddleocr_speech_page_group_with_json.ocr_prelim_groups_json_file
            tmp_ocr_file = Path("/tmp") / ocr_file.name
            self._paddleocr_speech_page_group_with_json.save_group(tmp_ocr_file)
            print(f'Saved new paddleocr text to file "{tmp_ocr_file}". Text:\n{new_paddleocr_text}')


app = typer.Typer()


@app.command(help="Prelim OCR Text Editor")
def main(
    volume: int,
    fanta_page: int,
    panel_num: int,
    easyocr_group_id: int,
    paddleocr_group_id: int,
) -> None:
    EditorApp(volume, fanta_page, panel_num, easyocr_group_id, paddleocr_group_id).run()


if __name__ == "__main__":
    app()
