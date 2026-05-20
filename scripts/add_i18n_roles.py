# -*- coding: utf-8 -*-
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[1] / "public" / "pages"

ROLE_MAP = {
    "admin": "coordinator",
    "supervisor": "supervisor",
    "student": "student",
}


def patch_file(path: Path, role: str) -> bool:
    text = path.read_text(encoding="utf-8")
    old = '<span>منسق</span>' if role == "coordinator" else None
    if role == "supervisor":
        old = '<span>مشرف</span>'
    elif role == "student":
        old = '<span>طالب</span>'
    if not old or old not in text:
        # try generic header badge
        import re

        pat = re.compile(
            r'(<span class="hidden sm:inline-flex[^"]*"[^>]*>\s*<i[^>]*></i>\s*)<span>([^<]+)</span>',
            re.DOTALL,
        )
        m = pat.search(text)
        if not m:
            return False
        new = f'{m.group(1)}<span data-i18n-role="{role}">{m.group(2)}</span>'
        text2 = pat.sub(new, text, count=1)
        if text2 != text:
            path.write_text(text2, encoding="utf-8", newline="\n")
            return True
        return False
    new = f'<span data-i18n-role="{role}">{old[7:-8]}</span>'
    if new in text:
        return False
    text2 = text.replace(old, new, 1)
    path.write_text(text2, encoding="utf-8", newline="\n")
    return True


def main():
    n = 0
    for folder, role in ROLE_MAP.items():
        d = PUBLIC / folder
        if not d.is_dir():
            continue
        for html in d.glob("*.html"):
            if patch_file(html, role):
                n += 1
                print("patched", html.name, role)
    print("done", n)


if __name__ == "__main__":
    main()
