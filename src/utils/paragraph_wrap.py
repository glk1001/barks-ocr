import textwrap


class ParagraphWrapper(textwrap.TextWrapper):
    def wrap(self, text: str) -> list[str]:
        paragraphs = text.split("\n")
        wrapped_lines = []

        # 1. Save the original configuration.
        original_initial = self.initial_indent
        original_subsequent = self.subsequent_indent

        try:
            for i, paragraph in enumerate(paragraphs):
                # 2. Logic: Only the very first paragraph (i==0) uses the 'initial_indent'.
                #    For all subsequent paragraphs (i>0), we force the wrapper to start
                #    with the 'subsequent_indent' so they align visually with the body.
                if i > 0:
                    self.initial_indent = original_subsequent

                # Standard wrap logic
                lines = textwrap.TextWrapper.wrap(self, paragraph)
                wrapped_lines.extend(lines)
        finally:
            # 3. Restore configuration so the instance works correctly if reused.
            self.initial_indent = original_initial
            self.subsequent_indent = original_subsequent

        return wrapped_lines


if __name__ == "__main__":
    text_indenter = ParagraphWrapper(
        width=40,  # Added width to demonstrate wrapping
        initial_indent="  ",
        subsequent_indent="        ",
    )

    text_lines = "line 1\nline 2\nline 3\nline 4 is longer to demonstrate wrapping behavior."
    indented_text = text_indenter.fill(f'"{12}": {text_lines}')

    print(indented_text)  # noqa: T201
