# ruff: noqa: E402
import json
from collections.abc import Callable
from pathlib import Path

import typer
from attr import dataclass
from barks_fantagraphics.barks_titles import BARKS_TITLE_DICT, BARKS_TITLES
from barks_fantagraphics.comic_book import get_page_str
from barks_fantagraphics.comics_consts import FONT_DIR, OPEN_SANS_FONT
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_title_from_volume_page
from barks_fantagraphics.comics_utils import get_abbrev_path, get_backup_file
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_BACKUP_DIR, OCR_PRELIM_DIR
from barks_fantagraphics.speech_groupers import OcrTypes, get_speech_page_group
from comic_utils.comic_consts import PNG_FILE_EXT
from comic_utils.common_typer_options import LogLevelArg
from comic_utils.pil_image_utils import load_pil_image_for_reading
from kivy.config import Config
from loguru import logger
from loguru_config import LoguruConfig

APP_LOGGING_NAME = "kpoe"

# Set the main window size using variables
MAIN_WINDOW_X = 2100
MAIN_WINDOW_Y = 20
MAIN_WINDOW_WIDTH = 2000
MAIN_WINDOW_HEIGHT = 1300

Config.set("graphics", "position", "custom")  # ty:ignore[unresolved-attribute]
Config.set("graphics", "left", MAIN_WINDOW_X)  # ty:ignore[unresolved-attribute]
Config.set("graphics", "top", MAIN_WINDOW_Y)  # ty:ignore[unresolved-attribute]
Config.set("graphics", "width", MAIN_WINDOW_WIDTH)  # ty:ignore[unresolved-attribute]
Config.set("graphics", "height", MAIN_WINDOW_HEIGHT)  # ty:ignore[unresolved-attribute]

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.core.window import Window

# noinspection PyUnresolvedReferences
from kivy.properties import (  # ty:ignore[unresolved-import]
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
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
MAX_NUM_PANELS = 8


# TODO: Duplicated in 'edit-page.py'.
def write_cropped_image_file(
    srce_image_file: Path, segments_file: Path, target_image_file: Path, panel: int
) -> None:
    if not (1 <= panel <= MAX_NUM_PANELS):
        msg = f'Srce image file: "{srce_image_file}" - invalid panel number "{panel}".'
        raise ValueError(msg)

    if not segments_file.is_file():
        logger.warning(f'Could not find segments file "{segments_file}". Returning full page.')
        image = load_pil_image_for_reading(srce_image_file)
        image.save(target_image_file, optimize=True, compress_level=9)
    else:
        with segments_file.open() as f:
            panel_segment_info = json.load(f)

        if not (0 < panel <= len(panel_segment_info["panels"])):
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
    panel_num: int
    group_id: str
    text: str


class EditorApp(App):
    text_str_easyocr = StringProperty()
    text_str_paddleocr = StringProperty()
    edit_label_easyocr = StringProperty("EasyOCR")
    edit_label_paddleocr = StringProperty("PaddleOCR")
    panel_heading_text = StringProperty()

    def __init__(
        self,
        volume: int,
        fanta_page: int,
        easyocr_group_id: int,
        paddleocr_group_id: int,
        panel_num: int,
    ) -> None:
        super().__init__()

        self._volume = volume
        self._fanta_page = get_page_str(fanta_page)
        self._displayed_panel_num = -1

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
        self._panel_image_widget = Image(size_hint_y=0.8, fit_mode="contain")
        self._decode_checkbox: CheckBox | None = None
        self._popup: Popup | None = None

        self._easyocr_speech_page_group = get_speech_page_group(
            self._comics_database,
            volume,
            self._title,
            OcrTypes.EASYOCR,
            self._fanta_page,
            self._dest_page,
        )
        self._paddleocr_speech_page_group = get_speech_page_group(
            self._comics_database,
            volume,
            self._title,
            OcrTypes.PADDLEOCR,
            self._fanta_page,
            self._dest_page,
        )

        self._easyocr_speech_groups = self._easyocr_speech_page_group.speech_groups
        self._paddleocr_speech_groups = self._paddleocr_speech_page_group.speech_groups

        panel_segments_dir = Path(
            self._comics_database.get_fantagraphics_panel_segments_volume_dir(self._volume)
        )
        self._panel_segments_file = panel_segments_dir / (self._fanta_page + ".json")

        self._set_easyocr_group_id(str(easyocr_group_id))
        self._set_paddleocr_group_id(str(paddleocr_group_id))

        if panel_num != -1:
            self._set_panel_num(panel_num)

        Window.bind(on_request_close=self.on_request_close)

    def build(self) -> Widget:
        self.text_str_easyocr = self._easyocr_speech_groups[self._easyocr_group_id].raw_ai_text
        self.text_str_paddleocr = self._paddleocr_speech_groups[
            self._paddleocr_group_id
        ].raw_ai_text

        return self._create_editor_widget()

    def on_request_close(self, *_args) -> bool:  # noqa: ANN002
        if (
            not self._easyocr_speech_page_group.has_group_changed()
            and not self._paddleocr_speech_page_group.has_group_changed()
        ):
            return False

        self._show_exit_popup()

        # Returning True prevents the window from closing immediately
        return True

    def _show_exit_popup(self) -> None:
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        content.add_widget(
            Label(text="Some speech items have changed.\nAre you sure you want to exit?")
        )

        button_layout = BoxLayout(spacing=10)

        yes_button = Button(text="Yes")
        yes_button.bind(on_press=self._stop_app)
        button_layout.add_widget(yes_button)

        no_button = Button(text="No")
        no_button.bind(on_press=lambda _btn: self._popup.dismiss())
        button_layout.add_widget(no_button)

        content.add_widget(button_layout)

        self._popup = Popup(
            title="Data Changed Without Save",
            content=content,
            size_hint=(None, None),
            size=(400, 200),
            auto_dismiss=False,
        )
        self._popup.open()

    def _stop_app(self, *_args) -> None:  # noqa: ANN002
        self._popup.dismiss()
        self.stop()

    def _on_easyocr_text_changed(self, instance: TextInput, _value: str) -> None:
        if not instance.focus:
            return

        self._easyocr_speech_groups[
            self._easyocr_group_id
        ].raw_ai_text = self._get_current_easyocr_text()

    def _on_paddleocr_text_changed(self, instance: TextInput, _value: str) -> None:
        if not instance.focus:
            return

        self._paddleocr_speech_groups[
            self._paddleocr_group_id
        ].raw_ai_text = self._get_current_paddleocr_text()

    def _set_easyocr_group_id(self, group_id: str) -> None:
        if group_id not in self._easyocr_speech_groups:
            msg = f"Unknown easyocr group id '{group_id}'."
            raise ValueError(msg)

        self._easyocr_group_id = group_id

        speech_group = self._easyocr_speech_groups[self._easyocr_group_id]
        panel_num = speech_group.panel_num

        self._easyocr_label = self._get_ocr_label(EASY_OCR, self._easyocr_group_id, panel_num)

        self.text_str_easyocr = self._encode_for_display(speech_group.raw_ai_text)
        panel_num = speech_group.panel_num
        self._set_panel_num(panel_num)

    def _set_paddleocr_group_id(self, group_id: str) -> None:
        if group_id not in self._paddleocr_speech_groups:
            msg = f"Unknown paddleocr group id '{group_id}'."
            raise ValueError(msg)

        self._paddleocr_group_id = group_id

        speech_group = self._paddleocr_speech_groups[self._paddleocr_group_id]
        panel_num = speech_group.panel_num

        self._paddleocr_label = self._get_ocr_label(PADDLE_OCR, self._paddleocr_group_id, panel_num)

        self.text_str_paddleocr = self._encode_for_display(speech_group.raw_ai_text)
        self._set_panel_num(panel_num)

    @staticmethod
    def _get_ocr_label(ocr_name: str, group_id: str, panel_num: int) -> str:
        return f"{ocr_name}: group_id: {group_id}; panel: {panel_num}"

    def _set_panel_num(self, panel_num: int) -> None:
        if self._displayed_panel_num == panel_num:
            return

        self._displayed_panel_num = panel_num

        self.panel_heading_text = f"Panel {self._displayed_panel_num}"

        new_source = str(self.get_panel_image_file(self._displayed_panel_num))
        if self._panel_image_widget.source:
            Path(self._panel_image_widget.source).unlink(missing_ok=True)
        self._panel_image_widget.source = new_source

    def _get_editor_info(self) -> str:
        easyocr_file = self._easyocr_speech_page_group.ocr_prelim_groups_json_file
        paddleocr_file = self._paddleocr_speech_page_group.ocr_prelim_groups_json_file
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
        content_layout.add_widget(self._get_bottom_layout())

        return content_layout

    def _get_right_layout(self) -> BoxLayout:
        right_layout = BoxLayout(orientation="vertical", spacing=10, size_hint_x=0.5)

        # Add spacer to align the checkbox below with the top of the text input
        # on the left. The spacer's height matches the label on the left.
        right_layout.add_widget(Widget(size_hint_y=None, height=30))

        # Top part: Checkbox
        checkbox_layout, self._decode_checkbox = self._add_decode_checkbox()
        right_layout.add_widget(checkbox_layout)

        # Top Spacer to center the image and heading
        right_layout.add_widget(Widget(size_hint_y=1))

        # Heading
        panel_heading = Label(
            text=self.panel_heading_text,
            size_hint_y=None,
            height=30,
            font_size="20sp",
            bold=True,
        )
        self.bind(panel_heading_text=panel_heading.setter("text"))
        right_layout.add_widget(panel_heading)

        # Image (takes up the most space in the center)
        self._panel_image_widget.size_hint_y = 8
        right_layout.add_widget(self._panel_image_widget)

        # Bottom Spacer to center the image and heading
        right_layout.add_widget(Widget(size_hint_y=1))

        # Bottom Info
        extra_info_label = Label(
            text=self._get_editor_info(),
            size_hint_y=2,  # Relative weight for the bottom area
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
        text_input_1.bind(text=self._on_easyocr_text_changed)
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
        text_input_2.bind(text=self._on_paddleocr_text_changed)
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
                logger.exception(f"Error converting text: {e}")

        decode_checkbox.bind(active=on_checkbox_active)

        checkbox_layout.add_widget(decode_checkbox)
        checkbox_layout.add_widget(decode_label)

        return checkbox_layout, decode_checkbox

    # noinspection PyTypeHints
    def get_panel_image_file(self, panel_num: int) -> Path:
        panel_image_file = Path("/tmp") / (  # noqa: S108
            f"{self._volume}-{self._fanta_page}-{panel_num}" + PNG_FILE_EXT
        )
        write_cropped_image_file(
            self._srce_image_file, self._panel_segments_file, panel_image_file, panel_num
        )
        return panel_image_file

    def _get_bottom_layout(self) -> BoxLayout:
        layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=10)

        select_btn = Button(text="Select EasyOCR Speech Item", size_hint_y=None, height=50)
        select_btn.bind(on_press=self._show_easyocr_speech_item_popup)
        layout.add_widget(select_btn)

        select_btn = Button(text="Select PaddleOCR Speech Item", size_hint_y=None, height=50)
        select_btn.bind(on_press=self._show_paddleocr_speech_item_popup)
        layout.add_widget(select_btn)

        layout.add_widget(self._get_save_button())

        return layout

    def _show_easyocr_speech_item_popup(self, _instance: Button) -> None:
        self._show_speech_item_popup(
            "Select EasyOCR Speech Item",
            self._get_easyocr_speech_items(),
            self._on_easyocr_speech_item_selected,
        )

    def _show_paddleocr_speech_item_popup(self, _instance: Button) -> None:
        self._show_speech_item_popup(
            "Select PaddleOCR Speech Item",
            self._get_paddleocr_speech_items(),
            self._on_paddleocr_speech_item_selected,
        )

    @staticmethod
    def _show_speech_item_popup(
        popup_title: str,
        items: list[SpeechItem],
        on_speech_item_selected: Callable[[SpeechItem], None],
    ) -> None:
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)

        scroll = ScrollView()
        list_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=5)
        list_layout.bind(minimum_height=list_layout.setter("height"))

        popup = Popup(title=popup_title, content=content, size_hint=(0.9, 0.8))

        def select_item(selected_item: SpeechItem) -> None:
            popup.dismiss()
            on_speech_item_selected(selected_item)

        for item in items:
            btn_text = f"{item.panel_num}({item.group_id}): {item.text.replace('\n', ' ')}"
            btn = Button(text=btn_text, font_name=OPEN_SANS_FONT, size_hint_y=None, height=40)
            # Use default argument i=item to capture the current item in the loop
            btn.bind(on_release=lambda _inst, i=item: select_item(i))
            list_layout.add_widget(btn)

        scroll.add_widget(list_layout)
        content.add_widget(scroll)

        # Close button
        close_btn = Button(text="Close", size_hint_y=None, height=40)
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)

        popup.open()

    def _get_easyocr_speech_items(self) -> list[SpeechItem]:
        return [
            SpeechItem(panel_num=data.panel_num, group_id=group_id, text=data.raw_ai_text or "")
            for group_id, data in self._easyocr_speech_groups.items()
        ]

    def _on_easyocr_speech_item_selected(self, speech_item: SpeechItem) -> None:
        self._set_easyocr_group_id(speech_item.group_id)

    def _get_paddleocr_speech_items(self) -> list[SpeechItem]:
        return [
            SpeechItem(panel_num=data.panel_num, group_id=group_id, text=data.raw_ai_text or "")
            for group_id, data in self._paddleocr_speech_groups.items()
        ]

    def _on_paddleocr_speech_item_selected(self, speech_item: SpeechItem) -> None:
        self._set_paddleocr_group_id(speech_item.group_id)

    def _get_save_button(self) -> Button:
        save_btn = Button(text="Save & Exit", size_hint_y=None, height=50)

        def on_save(_instance: Button) -> None:
            self._handle_save()
            self.stop()

        save_btn.bind(on_press=on_save)

        return save_btn

    def _get_current_easyocr_text(self) -> str:
        return (
            self._decode_from_display(self.text_str_easyocr)
            if self._decode_checkbox.active
            else self.text_str_easyocr
        )

    def _get_current_paddleocr_text(self) -> str:
        return (
            self._decode_from_display(self.text_str_paddleocr)
            if self._decode_checkbox.active
            else self.text_str_paddleocr
        )

    def _handle_save(self) -> None:
        ocr_file = self._easyocr_speech_page_group.ocr_prelim_groups_json_file
        ocr_backup_file = self._get_prelim_ocr_backup_file(ocr_file)
        if not self._easyocr_speech_page_group.save_group(backup_file=ocr_backup_file):
            logger.debug(f'Nothing changed in easyocr file "{ocr_file}".')
        else:
            logger.info(
                f'Saved new easyocr text to file "{ocr_file}".'
                f' Backed up up old file to "{ocr_backup_file}".'
            )

        ocr_file = self._paddleocr_speech_page_group.ocr_prelim_groups_json_file
        ocr_backup_file = self._get_prelim_ocr_backup_file(ocr_file)
        if not self._paddleocr_speech_page_group.save_group(backup_file=ocr_backup_file):
            logger.debug(f'Nothing changed in paddleocr file "{ocr_file}".')
        else:
            logger.info(
                f'Saved new paddleocr text to file "{ocr_file}".'
                f' Backed up old file to "{ocr_backup_file}".'
            )

    @staticmethod
    def _get_prelim_ocr_backup_file(ocr_file: Path) -> Path:
        return Path(
            str(get_backup_file(ocr_file)).replace(str(OCR_PRELIM_DIR), str(OCR_PRELIM_BACKUP_DIR))
        )


app = typer.Typer()
log_level = ""
log_filename = "kivy-prelim-ocr-editor.log"


@app.command(help="Prelim OCR Text Editor")
def main(
    volume: int,
    fanta_page: int,
    easyocr_group_id: int,
    paddleocr_group_id: int,
    panel_num: int = -1,
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    # Global variable accessed by loguru-config.
    global log_level  # noqa: PLW0603
    log_level = log_level_str
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    EditorApp(volume, fanta_page, easyocr_group_id, paddleocr_group_id, panel_num).run()


if __name__ == "__main__":
    app()
