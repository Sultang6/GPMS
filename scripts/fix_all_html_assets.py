# -*- coding: utf-8 -*-
"""Fix asset paths and base tag for all public HTML pages."""
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[1] / "public"

INLINE_BASE = """    <script>
      (function () {
        function gpmsPublicBase() {
          if (location.protocol === "file:") {
            var u = location.href.split("#")[0].split("?")[0];
            var i = u.toLowerCase().indexOf("/pages/");
            if (i >= 0) return u.slice(0, i + 1);
            return u.slice(0, u.lastIndexOf("/") + 1);
          }
          var p = location.pathname.replace(/\\\\/g, "/");
          var idx = p.indexOf("/pages/");
          if (idx >= 0) return p.slice(0, idx + 1);
          var slash = p.lastIndexOf("/");
          return slash >= 0 ? p.slice(0, slash + 1) : "/";
        }
        window.gpmsPublicBase = gpmsPublicBase;
        var base = document.createElement("base");
        base.href = gpmsPublicBase();
        document.head.appendChild(base);
      })();
    </script>
"""

OLD_GPMS_BASE = """    <script>
      (function () {
        var base = document.createElement("base");
        var pageUrl = location.href.split("#")[0].split("?")[0];
        var path = location.pathname.replace(/\\\\/g, "/");
        if (location.protocol === "file:") {
          base.href = pageUrl.slice(0, pageUrl.lastIndexOf("/") + 1);
        } else {
          var slash = path.lastIndexOf("/");
          base.href = slash >= 0 ? path.slice(0, slash + 1) : "/";
        }
        document.head.appendChild(base);
      })();
    </script>
"""


def fix_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    orig = text

    text = text.replace('<base href="/" />\n', "")
    text = text.replace("<base href='/' />\n", "")

    if OLD_GPMS_BASE.strip() in text:
        text = text.replace(OLD_GPMS_BASE, INLINE_BASE)
    elif INLINE_BASE.strip() not in text and "<head>" in text:
        text = text.replace("<head>\n", "<head>\n" + INLINE_BASE, 1)

    text = text.replace('href="/css/GPMS.css"', 'href="css/GPMS.css"')
    text = text.replace('src="/js/', 'src="js/')

    text = text.replace('href="/pages/', 'href="pages/')
    text = text.replace('href="/GPMS.html', 'href="GPMS.html')
    text = text.replace("href='/pages/", "href='pages/")
    text = text.replace("href='/GPMS.html", "href='GPMS.html")

    if text != orig:
        path.write_text(text, encoding="utf-8", newline="\n")
        return True
    return False


def main():
    n = 0
    for html in PUBLIC.rglob("*.html"):
        if fix_file(html):
            n += 1
            print("fixed:", html.relative_to(PUBLIC))
    print("done,", n, "files")


if __name__ == "__main__":
    main()
