# ruff: noqa: E402
from attr import dataclass

import json
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

from kivy.app import App
from kivy.core.image import Image as CoreImage

# noinspection PyProtectedMember
from kivy.core.image import Texture
from kivy.core.text import LabelBase

# noinspection PyUnresolvedReferences
from kivy.properties import (  # ty:ignore[unresolved-import]
    ObjectProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

# TODO: Duplicated in 'font_manager.py'.
# Set up custom fonts.
LabelBase.register(
    name=OPEN_SANS_FONT,
    fn_regular=str(FONT_DIR / "OpenSans-Medium.ttf"),
    fn_bold=str(FONT_DIR / "OpenSans-Bold.ttf"),
    fn_italic=str(FONT_DIR / "OpenSans-MediumItalic.ttf"),
    fn_bolditalic=str(FONT_DIR / "OpenSans-BoldItalic.ttf"),
)

EASY_OCR = "EasyOCR"
PADDLE_OCR = "PaddleOCR"


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


@dataclass
class SpeechItem:
    group_id: str
    text: str


class EditorApp(App):
    text_str_easyocr = StringProperty()
    text_str_paddleocr = StringProperty()
    edit_label_easyocr = StringProperty("EasyOCR")
    edit_label_paddleocr = StringProperty("PaddleOCR")
    panel_heading_text = StringProperty()
    panel_image_texture = ObjectProperty(allownone=True)

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
        self._decode_checkbox: CheckBox | None = None
        self._easyocr_label = self._get_ocr_label(EASY_OCR, self._easyocr_group_id)
        self._paddleocr_label = self._get_ocr_label(PADDLE_OCR, self._paddleocr_group_id)

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

        self._set_panel_num(panel_num)

    def build(self) -> Widget:
        self.text_str_easyocr = self._easyocr_speech_page_group_with_json.speech_page_group[
            "speech_groups"
        ][self._easyocr_group_id]["raw_ai_text"]
        self.text_str_paddleocr = self._paddleocr_speech_page_group_with_json.speech_page_group[
            "speech_groups"
        ][self._paddleocr_group_id]["raw_ai_text"]

        return self._create_editor_widget()

    @staticmethod
    def _get_ocr_label(ocr_name: str, group_id: str) -> str:
        return f"{ocr_name}: group_id: {group_id}"

    def _set_panel_num(self, panel_num: int) -> None:
        self.panel_heading_text = f"Panel {panel_num}"
        self.panel_image_texture = self.get_panel_image_texture(panel_num)

    def _get_editor_info(self) -> str:
        easyocr_file = self._easyocr_speech_page_group_with_json.ocr_prelim_groups_json_file
        paddleocr_file = self._paddleocr_speech_page_group_with_json.ocr_prelim_groups_json_file
        return (
            f"Title: {BARKS_TITLES[self._title]}\n"
            f"Volume: {self._volume}\n"
            f"Fanta Page: {self._fanta_page}\n"
            f'EasyOCR file: {get_abbrev_path(easyocr_file)}"\n'
            f'PaddleOCR file: {get_abbrev_path(paddleocr_file)}"\n'
            f'Image file: {get_abbrev_path(self._srce_image_file)}"\n'
            f'Segments file: {get_abbrev_path(self._panel_segments_file)}"\n'
        )

    @staticmethod
    def _encode_for_display(text: str) -> str:
        return text.encode("unicode_escape").decode("utf-8").replace(r"\n", "\n")

    @staticmethod
    def _decode_from_display(text: str) -> str:
        return text.replace("\n", r"\n").encode("utf-8").decode("unicode_escape")

    def _create_editor_widget(self) -> BoxLayout:
        content_layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        editor_area = BoxLayout(orientation="horizontal", spacing=10)

        # Add widgets to editor layout
        right_layout = self._get_right_layout()
        text_layout = self._get_left_layout()

        editor_area.add_widget(text_layout)
        editor_area.add_widget(right_layout)

        # Add widgets to content layout
        content_layout.add_widget(editor_area)
        content_layout.add_widget(self._get_save_button())

        return content_layout

    def _get_right_layout(self) -> BoxLayout:
        right_layout = BoxLayout(orientation="vertical", size_hint_x=0.5)

        # Add spacer widget to move CheckBox down.
        right_layout.add_widget(Widget(size_hint_y=None, height=35))
        checkbox_layout, self._decode_checkbox = self._add_decode_checkbox()
        right_layout.add_widget(checkbox_layout)

        # Add spacer widget to move panel heading down.
        right_layout.add_widget(Widget(size_hint_y=None, height=235))
        panel_heading = Label(
            text=self.panel_heading_text,
            size_hint_y=None,
            height=30,
            font_size="20sp",
            bold=True,
        )
        self.bind(panel_heading_text=panel_heading.setter("text"))
        panel_heading.bind(text=self.setter("panel_heading_text"))
        right_layout.add_widget(panel_heading)

        # Add the panel image.
        panel_image_widget = Image(
            texture=self.panel_image_texture,
            size_hint_y=0.8,
            allow_stretch=True,
            keep_ratio=True,
        )
        self.bind(panel_image_texture=panel_image_widget.setter("texture"))
        panel_image_widget.bind(texture=self.setter("panel_image_texture"))
        right_layout.add_widget(panel_image_widget)

        # Add the extra info.
        extra_info_label = Label(
            text=self._get_editor_info(),
            size_hint_y=0.2,
            font_size="17sp",
            halign="left",
            valign="top",
            padding=10,
        )
        extra_info_label.bind(size=extra_info_label.setter("text_size"))
        right_layout.add_widget(extra_info_label)

        return right_layout

    def _get_left_layout(self) -> BoxLayout:
        text_layout = BoxLayout(orientation="vertical", spacing=10, size_hint_x=0.5)

        label_1 = Label(text=self.edit_label_easyocr, bold=True, size_hint_y=None, height=30)
        self.bind(edit_label_easyocr=label_1.setter("text"))
        label_1.bind(text=self.setter("edit_label_easyocr"))

        text_input_1 = TextInput(
            text=self.text_str_easyocr,
            font_name=OPEN_SANS_FONT,
            font_size="20sp",
            multiline=True,
            size_hint_y=1,
            padding=10,
            hint_text="Edit EasyOCR text here...",
        )
        self.bind(text_str_easyocr=text_input_1.setter("text"))
        text_input_1.bind(text=self.setter("text_str_easyocr"))
        self.text_str_easyocr = self._encode_for_display(self.text_str_easyocr)

        label_2 = Label(text=self.edit_label_paddleocr, bold=True, size_hint_y=None, height=30)
        self.bind(edit_label_paddleocr=label_2.setter("text"))
        label_2.bind(text=self.setter("edit_label_paddleocr"))

        text_input_2 = TextInput(
            text=self.text_str_paddleocr,
            font_size="20sp",
            font_name=OPEN_SANS_FONT,
            multiline=True,
            size_hint_y=1,
            padding=10,
            hint_text="Edit PaddleOCR text here...",
        )
        self.bind(text_str_paddleocr=text_input_2.setter("text"))
        text_input_2.bind(text=self.setter("text_str_paddleocr"))
        self.text_str_paddleocr = self._encode_for_display(self.text_str_paddleocr)

        def update_diff_labels(*_args) -> None:  # noqa: ANN002
            try:
                t1 = text_input_1.text
                t2 = text_input_2.text
                if self._decode_checkbox.active:  # If True, text is encoded for display
                    t1 = self._decode_from_display(t1)
                    t2 = self._decode_from_display(t2)

                are_different = t1 != t2

                if are_different:
                    self.edit_label_easyocr = f"DIFFS -- {self._easyocr_label}"
                    self.edit_label_paddleocr = f"DIFFS -- {self._paddleocr_label}"
                    label_1.color = (1, 0, 0, 1)  # Red
                    label_2.color = (1, 0, 0, 1)  # Red
                else:
                    self.edit_label_easyocr = self._easyocr_label
                    self.edit_label_paddleocr = self._paddleocr_label
                    label_1.color = (1, 1, 1, 1)  # Default/White
                    label_2.color = (1, 1, 1, 1)  # Default/White
            except UnicodeDecodeError:
                # During typing, an invalid escape sequence might exist temporarily.
                # We can just ignore the update in this case.
                pass

        text_input_1.bind(text=update_diff_labels)
        text_input_2.bind(text=update_diff_labels)

        text_layout.add_widget(label_1)
        text_layout.add_widget(text_input_1)
        text_layout.add_widget(label_2)
        text_layout.add_widget(text_input_2)

        update_diff_labels()

        return text_layout

    def _add_decode_checkbox(self) -> tuple[BoxLayout, CheckBox]:
        checkbox_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=30)

        decode_checkbox = CheckBox(active=True, size_hint_x=None, width=30)
        decode_label = Label(text="Show Unicode", halign="left", valign="middle")
        decode_label.bind(size=decode_label.setter("text_size"))

        def on_checkbox_active(_instance: CheckBox, value: bool) -> None:
            try:
                t1 = self.text_str_easyocr
                t2 = self.text_str_paddleocr
                if value:
                    # Decoded -> Encoded
                    self.text_str_easyocr = self._encode_for_display(t1)
                    self.text_str_paddleocr = self._encode_for_display(t2)
                else:
                    # Encoded -> Decoded
                    self.text_str_easyocr = self._decode_from_display(t1)
                    self.text_str_paddleocr = self._decode_from_display(t2)
            except UnicodeDecodeError as e:
                print(f"Error converting text: {e}")

        decode_checkbox.bind(active=on_checkbox_active)

        checkbox_layout.add_widget(decode_checkbox)
        checkbox_layout.add_widget(decode_label)

        return checkbox_layout, decode_checkbox

    # noinspection PyTypeHints
    def get_panel_image_texture(self, panel_num: int) -> Texture:
        panel_image_file = Path("/tmp") / (f"{self._volume}-{self._fanta_page}" + PNG_FILE_EXT)
        write_cropped_image_file(
            self._srce_image_file, self._panel_segments_file, panel_image_file, panel_num
        )
        return CoreImage(str(panel_image_file)).texture

    def _get_save_button(self) -> Button:
        save_btn = Button(text="Save & Exit", size_hint_y=None, height=50)

        def on_save(_instance: Button) -> None:
            try:
                if self._decode_checkbox.active:
                    edited_text_1 = self._decode_from_display(self.text_str_easyocr)
                    edited_text_2 = self._decode_from_display(self.text_str_paddleocr)
                else:
                    edited_text_1 = self.text_str_easyocr
                    edited_text_2 = self.text_str_paddleocr
            except UnicodeDecodeError as e:
                print(f"Error decoding text: {e}")
                return

            self._handle_result(edited_text_1, edited_text_2)
            self.stop()

        save_btn.bind(on_press=on_save)

        return save_btn

    def _handle_result(self, new_easyocr_text: str, new_paddleocr_text: str) -> None:
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
