# -*- coding: utf-8 -*-
from pathlib import Path

pages = Path(__file__).resolve().parents[1] / "public" / "pages"
needle = '<script src="js/gpms-lang-toggle.js"></script>'
extra = needle + '\n    <script src="js/gpms-page-i18n.js"></script>'
n = 0
for f in pages.rglob("*.html"):
    t = f.read_text(encoding="utf-8")
    if "gpms-page-i18n.js" in t:
        continue
    if needle in t:
        t2 = t.replace(needle, extra, 1)
    elif '<script src="js/GPMS.js"></script>' in t:
        t2 = t.replace(
            '<script src="js/GPMS.js"></script>',
            '<script src="js/GPMS.js"></script>\n'
            '    <script src="js/gpms-lang-toggle.js"></script>\n'
            '    <script src="js/gpms-page-i18n.js"></script>',
            1,
        )
    else:
        continue
    if t2 != t:
        f.write_text(t2, encoding="utf-8", newline="\n")
        n += 1
        print(f.name)
print("done", n)
