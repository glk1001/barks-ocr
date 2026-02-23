# ruff: noqa: T201

from barks_ocr.utils.gemini_ai import CLIENT


def main() -> None:
    print(f"{'Model Name':<50} | {'Display Name'}")
    print("-" * 80)

    for model in CLIENT.models.list():
        if "gemini" in model.name.lower():  # ty:ignore[unresolved-attribute]
            print(f"{model.name:<50} | {model.display_name}")


if __name__ == "__main__":
    main()
