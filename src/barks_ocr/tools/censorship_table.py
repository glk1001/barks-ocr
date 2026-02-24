import csv
from pathlib import Path

import polars as pl
from great_tables import GT, html, loc, md, style
from PIL import Image

ROOT_DIR = Path("/home/greg/Books/Carl Barks")
CSV_DIR = ROOT_DIR / "Projects" / "Barks Reader"


def get_censorship_fixes_table(file: Path) -> GT:
    df = pl.read_csv(file)

    table = (
        GT(df)
        # .tab_header(
        #     title=md("**Censorship Fixes and Other Changes**"),
        #     subtitle=md("Includes fixes for Fantagraphics printing and coloring glitches"),
        # )
        # .tab_options(heading_padding="1%")
        #        .opt_row_striping(row_striping=True)
        #        .tab_spanner(label=md("**Changes**"), columns=["Change_From", "Change_To"])
        .tab_stub(rowname_col="Story")
        .tab_stubhead(label="Story")
        .tab_style(style=style.text(weight="bold"), locations=loc.stubhead())
        .cols_label(
            Change_From=html("From"),
            Change_To=html("To"),
            Page_Panel=html("Panel"),
        )
        .tab_style(
            style=style.text(weight=500),  # ty: ignore[invalid-argument-type]
            locations=loc.body(columns="Story"),
        )
        .cols_width(
            cases={
                "Story": "150px",
                "Change_From": "335px",
                "Change_To": "335px",
                "Page_Panel": "50px",
            }
        )
    )

    table = table.tab_style(style=style.text(weight="bold"), locations=loc.column_labels())
    # Apply the conditional centering style
    required_columns = df.drop("Page_Panel").columns
    table = table.tab_style(
        style=style.text(align="left"),
        locations=[
            loc.body(columns=col_name, rows=pl.col(col_name) == '"')
            for col_name in required_columns
        ],
    )
    required_columns = df.drop("Story").columns
    table = table.tab_style(
        style=style.text(style="italic", weight=500),  # ty: ignore[invalid-argument-type]
        locations=[loc.body(columns=col_name) for col_name in required_columns],
    )
    # table = table.tab_style(
    #     style=style.fill(color="lightyellow"),  # Set the fill color
    #     locations=loc.body(columns="Story"),  # Target the body of "col_b"
    # )
    return table  # noqa: RET504


def split_rows_into_pages(pg_size: int, rows: list, first_page_reduction: int = 0) -> dict:
    pages = {}
    page_num = 1
    row_list = []
    row_count = 0
    current_pg_size = pg_size - first_page_reduction
    prev_non_empty_cols = list(rows[0])
    for index, row in enumerate(rows):
        if row_count == 0:
            for i, col in enumerate(row):
                if col == '"':
                    row[i] = prev_non_empty_cols[i]

        row_list.append(row)
        row_count += 1

        prev_non_empty_cols = [
            col if col != '"' else prev_non_empty_col
            for col, prev_non_empty_col in zip(row, prev_non_empty_cols, strict=True)
        ]

        if (row_count == current_pg_size) or (index + 1 == len(rows)):
            pages[page_num] = row_list
            row_list = []
            row_count = 0
            page_num += 1
            current_pg_size = pg_size  # remaining pages use full size

    return pages


def main() -> None:
    page_size = 36
    file = CSV_DIR / "censorship-fixes-simple.csv"
    with file.open("r", newline="") as csvfile:
        csv_reader = csv.reader(csvfile)
        header = next(csv_reader)
        csv_rows = list(csv_reader)

    pages = split_rows_into_pages(page_size, csv_rows, first_page_reduction=4)
    num_pages = len(pages)

    # Break a censorship fixes list into pages with white backgrounds.
    # These can be added to the Gimp project where the background is
    # easily removed. Then apply contrast = -70% to the remaining black text.
    for page in range(1, num_pages + 1):
        page_rows = pages[page]

        temp_file = Path("/tmp/temp.csv")  # noqa: S108
        with temp_file.open("w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(header)
            csv_writer.writerows(page_rows)  # Writes all rows at once

        gt_table = get_censorship_fixes_table(temp_file)
        gt_table.show()

        image_file = Path(f"/tmp/censorship-fixes-page-{page}.png")  # noqa: S108
        gt_table.save(str(image_file), scale=2.5, expand=10)
        Image.open(image_file).convert("RGBA").save(image_file)

        if page == 1:
            break  # noqa: ERA001


if __name__ == "__main__":
    main()
