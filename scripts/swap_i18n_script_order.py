# -*- coding: utf-8 -*-
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[1] / "public"

OLD = """    <script src="js/gpms-i18n.js"></script>
    <script src="js/gpms-i18n-extra.js"></script>"""

NEW = """    <script src="js/gpms-i18n-extra.js"></script>
    <script src="js/gpms-i18n.js"></script>"""


def main():
    n = 0
    for html in PUBLIC.rglob("*.html"):
        text = html.read_text(encoding="utf-8")
        if OLD in text:
            html.write_text(text.replace(OLD, NEW), encoding="utf-8", newline="\n")
            n += 1
    print("swapped", n, "files")


if __name__ == "__main__":
    main()
