import csv
from pathlib import Path

import polars as pl
from barks_fantagraphics.censorship_fixes import CENSORSHIP_FIXES_HEADER, read_censorship_fixes
from great_tables import GT, html, loc, style
from PIL import Image, ImageChops

# Written by `barks-ocr-censorship-csv`; see `tools/censorship_csv.py` for how the
# derived columns are worked out.
COLUMN_WIDTHS = {
    "Volume": "60px",
    "Image": "55px",
    "Fanta_page": "60px",
    "Page_Panel": "65px",
    "Story": "150px",
    "Change_From": "350px",
    "Change_To": "350px",
}

# The drawn columns. Two of them are not in the CSV as such:
#   * Page_Panel is Comic_page and Panel joined, built by `_add_page_panel_column`.
#   * Error_type is left out - each table holds one kind of fix, so the value is
#     constant down the whole document and the column would say nothing.
RENDERED_COLUMNS = list(COLUMN_WIDTHS)

# The columns drawn in italics. Named rather than taken as "everything but Story", which
# is how it used to be worked out: that swept up Volume, Image and Fanta_page the moment
# they were added, and an italic page number reads as an aside rather than a reference.
ITALIC_COLUMNS = ("Page_Panel", "Change_From", "Change_To")

# `_remove_white_background` turns a pixel transparent when every channel exceeds this,
# so anything at or below it is what survives into the finished page.
WHITE_THRESHOLD = 127

# The hairline between rows. great_tables' own default is #d3d3d3 (211), which the Gimp
# pipeline deletes outright - every channel is above WHITE_THRESHOLD - so the tables have
# been coming out with no rules at all. A rule has to sit at or below that threshold to
# survive, which makes #787878 (120) about the lightest hairline this pipeline can carry.
ROW_RULE_COLOR = "#787878"

# One table per Error_type, each written as its own set of page images numbered from 1.
# Exactly one story carries both kinds, so this splits almost nothing between the two.
ERROR_TYPE_FILE_STEMS = {
    "censorship": "censorship-fixes",
    "error": "error-fixes",
}

# The mark a repeated value is replaced with. A straight quote, as the source CSV used
# before the values were written out in full - it stays clearly distinct from the curly
# quotes inside Change_From and Change_To.
DITTO_MARK = '"'
#
# The marks are left-aligned, following each column's own alignment, rather than centred.
# The classical rule is that a ditto sits centred under the entry it repeats, and centring
# it in the column only coincides with that when the entry fills the column. Here it does
# not: in Change_From and Change_To a centred mark floats 175px out into white space with
# nothing above it, and in Story the names vary too much in length to have a stable
# centre. Left-aligned puts it under the start of the entry in every column.

# Columns whose value is replaced when it repeats the row above, within a rendered page,
# mapped to the column that must also be unchanged for the replacement to apply.
# Comic_page and Panel are absent because they always show: they are what identifies the
# row.
#
# The Story guard keeps a repeat from collapsing across a story boundary. Two stories
# often share a fix ("[wrong hat colour]"), and dittoing the second reads as though the
# rows were one group.
REPEAT_SUPPRESSED_COLUMNS = {
    "Volume": None,
    "Image": None,
    "Fanta_page": None,
    "Story": None,
    "Change_From": "Story",
    "Change_To": "Story",
}

# Of those, the columns that go blank on a repeat instead of taking a ditto mark. A
# volume heads a block of rows rather than being a value you would say "same as above"
# about, and one volume can run for most of a page, so a ditto there is a stripe of quote
# marks down a narrow column that tells the reader nothing.
BLANK_ON_REPEAT = frozenset({"Volume"})


def _add_page_panel_column(df: pl.DataFrame) -> pl.DataFrame:
    """Join Comic_page and Panel into the single `Page_Panel` reference that is drawn.

    Page 11 panel 5 reads as "11-5". Three other forms occur: a whole-story row has
    neither and stays blank, a whole-page row has no panel and is just "3", and the one
    two-panel row becomes "6-7,8".
    """
    return df.with_columns(
        pl.when(pl.col("Comic_page") == "")
        .then(pl.lit(""))
        .when(pl.col("Panel") == "")
        .then(pl.col("Comic_page"))
        .otherwise(pl.concat_str(["Comic_page", "Panel"], separator="-"))
        .alias("Page_Panel")
    )


def get_censorship_fixes_table(file: Path) -> GT:
    # Every column stays a string: `Image` has leading zeros ("007"), `Fanta_page` can be
    # a folio ("188a"), and `Panel` can list two panels ("7,8").
    # An empty cell is a real blank, not a missing value - without this great_tables
    # renders every one of them as "None".
    df = pl.read_csv(file, infer_schema_length=0).fill_null("")
    df = _add_page_panel_column(df).select(RENDERED_COLUMNS)

    # noinspection PyArgumentList
    table = (
        GT(df)
        .cols_label(
            Fanta_page=html("Fanta Page"),
            Page_Panel=html("Page-Panel"),
            Change_From=html("Change From"),
            Change_To=html("Change To"),
        )
        .tab_style(
            # great_tables types `weight` as a 4-value Literal, but it passes the value
            # straight through to CSS `font-weight`, where numeric weights are valid.
            # pyrefly: ignore[bad-argument-type]
            style=style.text(weight=500),  # ty: ignore[invalid-argument-type]
            locations=loc.body(columns="Story"),
        )
        .cols_width(cases=COLUMN_WIDTHS)
        # Right-justified so the page number lines up down the column, whether the
        # reference is "3", "11-5" or "6-7,8". The padding keeps it off the story name,
        # which is left-aligned in the very next column.
        .cols_align(align="right", columns="Page_Panel")
        .tab_style(style=style.css("padding-right: 8px"), locations=loc.body("Page_Panel"))
        .tab_options(table_body_hlines_color=ROW_RULE_COLOR, table_body_hlines_width="1px")
    )

    table = table.tab_style(style=style.text(weight="bold"), locations=loc.column_labels())
    table = table.tab_style(
        # Numeric CSS font-weight, as above.
        # pyrefly: ignore[bad-argument-type]
        style=style.text(style="italic", weight=500),  # ty: ignore[invalid-argument-type]
        locations=[loc.body(columns=col_name) for col_name in ITALIC_COLUMNS],
    )
    return table  # noqa: RET504


def split_rows_by_error_type(
    header: list[str], rows: list[list[str]]
) -> list[tuple[str, list[list[str]]]]:
    """Split the rows into one table per Error_type.

    Row order within a table is left alone: the CSV is already sorted into book order by
    `barks-ocr-censorship-csv`.

    Args:
        header: The CSV column names, in order.
        rows: All the data rows.

    Returns:
        One `(file stem, rows)` pair per non-empty table, `ERROR_TYPE_FILE_STEMS` order
        first. An Error_type with no configured stem still gets a table, named after the
        value itself, so no row is ever dropped.

    """
    column = header.index("Error_type")
    seen = list(dict.fromkeys(row[column] for row in rows))
    order = list(ERROR_TYPE_FILE_STEMS) + [t for t in seen if t not in ERROR_TYPE_FILE_STEMS]

    tables = [
        (ERROR_TYPE_FILE_STEMS.get(error_type, f"{error_type}-fixes"), group)
        for error_type in order
        if (group := [row for row in rows if row[column] == error_type])
    ]
    return tables  # noqa: RET504


def split_rows_into_pages(pg_size: int, rows: list, first_page_reduction: int = 0) -> dict:
    pages = {}
    page_num = 1
    row_list = []
    row_count = 0
    current_pg_size = pg_size - first_page_reduction
    for index, row in enumerate(rows):
        row_list.append(row)
        row_count += 1

        if (row_count == current_pg_size) or (index + 1 == len(rows)):
            pages[page_num] = row_list
            row_list = []
            row_count = 0
            page_num += 1
            current_pg_size = pg_size  # remaining pages use full size

    return pages


def ditto_repeated_values(header: list[str], rows: list[list[str]]) -> list[list[str]]:
    """Replace each cell that repeats the one above it with a ditto mark, or a blank.

    Applied per rendered page, after the rows are split, so the first row of every page
    always carries its full values - which is what the ditto marks in the source CSV
    could not do, since they referred back across page breaks.

    A blank never takes a ditto: two whole-story rows share an empty Image and Fanta_page,
    and a quote mark under an empty cell claims there was a value to repeat.

    Args:
        header: The CSV column names, in order.
        rows: One rendered page's data rows.

    Returns:
        The same rows with repeated values replaced by `DITTO_MARK`, or by a blank for
        the `BLANK_ON_REPEAT` columns.

    """
    suppressed = [
        (
            header.index(name),
            None if guard is None else header.index(guard),
            "" if name in BLANK_ON_REPEAT else DITTO_MARK,
        )
        for name, guard in REPEAT_SUPPRESSED_COLUMNS.items()
        if name in header
    ]

    dittoed = []
    previous: list[str] = []
    for row in rows:
        out = list(row)
        for column, guard, replacement in suppressed:
            if not previous or not row[column] or row[column] != previous[column]:
                continue
            if guard is None or row[guard] == previous[guard]:
                out[column] = replacement
        dittoed.append(out)
        previous = list(row)

    return dittoed


# The transparent border each finished page keeps, matching what great_tables' own
# `expand` produced before `_trim_vertical_padding` started tightening the pages.
PAGE_MARGIN = 35


def _trim_vertical_padding(image_file: Path, margin: int = PAGE_MARGIN) -> None:
    """Trim a page down to its content height, in-place, keeping the canvas width.

    `GT.save` resizes the browser window and then screenshots it, and on a table this
    wide the capture sometimes wins that race and comes back the height of the whole
    6000px window. The extra space is empty, so trimming to the content makes the output
    the same every run. Only the height is trimmed: the pages are stacked in a Gimp
    project, so they must all keep the same width.

    Args:
        image_file: The RGBA page image, already background-removed.
        margin: Transparent border to leave above and below the content.

    """
    img = Image.open(image_file)
    bbox = img.getchannel("A").getbbox()
    if bbox is None:
        return

    top = max(0, bbox[1] - margin)
    bottom = min(img.height, bbox[3] + margin)
    if (top, bottom) == (0, img.height):
        return

    img.crop((0, top, img.width, bottom)).save(image_file)


def _remove_white_background(image_file: Path, threshold: int = WHITE_THRESHOLD) -> None:
    """Replace near-white pixels with transparency in-place."""
    img = Image.open(image_file).convert("RGBA")
    r, g, b, _ = img.split()
    # Build a mask that is 255 where all three channels exceed the threshold.
    is_white = ImageChops.multiply(
        ImageChops.multiply(
            r.point(lambda v: 255 if v > threshold else 0),
            g.point(lambda v: 255 if v > threshold else 0),
        ),
        b.point(lambda v: 255 if v > threshold else 0),
    )
    # Invert: white pixels → alpha=0 (transparent), others → alpha=255 (opaque).
    img.putalpha(is_white.point(lambda v: 255 - v))
    img.save(image_file)


# noinspection PyArgumentList
def _render_page(header: list[str], page_rows: list[list[str]], image_file: Path) -> None:
    """Render one page of a table to a background-removed PNG.

    Args:
        header: The CSV column names, in order.
        page_rows: The rows on this page, already dittoed.
        image_file: Where to write the PNG.

    """
    temp_file = Path("/tmp/temp.csv")  # noqa: S108
    with temp_file.open("w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(header)
        csv_writer.writerows(page_rows)  # Writes all rows at once

    gt_table = get_censorship_fixes_table(temp_file)
    gt_table.save(str(image_file), scale=2.5, expand=10)
    _remove_white_background(image_file)
    _trim_vertical_padding(image_file)


def main() -> None:
    page_size = 36
    header = CENSORSHIP_FIXES_HEADER
    csv_rows = [row.as_cells() for row in read_censorship_fixes()]

    # Break each fixes list into pages with white backgrounds. These can be added to the
    # Gimp project where the background is easily removed. Then apply contrast = -70% to
    # the remaining black text.
    #
    # The censorship fixes and the printing errors are two separate tables, each numbered
    # from page 1, so each is its own document.
    for file_stem, table_rows in split_rows_by_error_type(header, csv_rows):
        pages = split_rows_into_pages(page_size, table_rows, first_page_reduction=4)
        for page, page_rows in pages.items():
            image_file = Path(f"/tmp/{file_stem}-page-{page}.png")  # noqa: S108
            _render_page(header, ditto_repeated_values(header, page_rows), image_file)


if __name__ == "__main__":
    main()
