#!/usr/bin/env python3
"""Static site generator for the 100-days-of-inference-engineering GitHub Pages site.

Renders README.md to HTML, copies images, and writes everything to _site/.

Usage: python scripts/build_site.py
Deps:  pip install markdown pymdown-extensions pygments mdx-truly-sane-lists
"""

import html
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
ASSETS = Path(__file__).resolve().parent / "assets"

REPO_URL = "https://github.com/pavelsimo/100-days-of-inference-engineering"
BLOB_URL = f"{REPO_URL}/blob/main/"
SITE_URL = "https://pavelsimo.github.io/100-days-of-inference-engineering/"

IMAGE_DIR = ROOT / "images"
IMAGE_EXTS = {".png", ".gif", ".jpg", ".jpeg", ".svg", ".webp"}

MD_EXTENSIONS = [
    "tables",
    "mdx_truly_sane_lists",  # GitHub-style 2-space nested lists
    "toc",
    "pymdownx.superfences",
    "pymdownx.highlight",
    "pymdownx.arithmatex",
]
MD_CONFIG = {
    "mdx_truly_sane_lists": {"nested_indent": 2},
    "pymdownx.highlight": {"css_class": "highlight", "guess_lang": False},
    "pymdownx.arithmatex": {"generic": True},
    "toc": {"permalink": False},
}

KATEX_HEAD = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{delimiters:[
    {left:'\\\\[',right:'\\\\]',display:true},
    {left:'\\\\(',right:'\\\\)',display:false}]})"></script>
"""

# Social / link-preview metadata (Open Graph + Twitter Card).
SOCIAL_META = """<meta name="description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="100 Days of Inference Engineering">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{page_url}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">"""

DEFAULT_DESCRIPTION = (
    "100 days of inference engineering: day-by-day progress log."
)


def social_meta(title: str, description: str, path: str) -> str:
    return SOCIAL_META.format(
        title=html.escape(title, quote=True),
        description=html.escape(description, quote=True),
        page_url=SITE_URL + path,
    )

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{social_meta}
<script>try{{if(localStorage.getItem('theme')==='light')document.documentElement.classList.add('light')}}catch(e){{}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/style.css">{extra_head}
</head>
<body>

<header class="site">
  <h1 class="site-title"><a href="{root}index.html">100 Days of <span class="accent">Inference</span> Engineering</a></h1>
  <div class="subtitle">{subtitle}</div>
</header>

<nav class="pipeline">
  <a href="{root}index.html"{active_home}>Home</a>
  <a href="{repo_url}">GitHub</a>
  <button id="btnTheme" type="button">&#9675; Theme</button>
</nav>

{content}

<footer class="site">
  <a href="{repo_url}">pavelsimo/100-days-of-inference-engineering</a>
</footer>

<script>
(() => {{
  const btn = document.getElementById('btnTheme');
  const sync = () => btn.textContent =
    document.documentElement.classList.contains('light') ? '\\u25CF Dark' : '\\u25CB Light';
  btn.onclick = () => {{
    const light = document.documentElement.classList.toggle('light');
    try {{ localStorage.setItem('theme', light ? 'light' : 'dark'); }} catch (e) {{}}
    sync();
  }};
  sync();
}})();
</script>
</body>
</html>
"""


def md_to_html(text: str) -> str:
    return markdown.markdown(text, extensions=MD_EXTENSIONS, extension_configs=MD_CONFIG)


def render_page(*, title, subtitle, content, root="", active="", math=False,
                path="", description=DEFAULT_DESCRIPTION) -> str:
    return PAGE_TEMPLATE.format(
        title=title,
        subtitle=subtitle,
        content=content,
        root=root,
        repo_url=REPO_URL,
        social_meta=social_meta(title, description, path),
        extra_head=KATEX_HEAD if math else "",
        active_home=' class="active"' if active == "home" else "",
    )


def rewrite_readme_links(html: str) -> str:
    """Point repo-relative links at the right place on the site (or GitHub)."""

    def repl(m):
        attr, url = m.group(1), m.group(2)
        if url.startswith(("http://", "https://", "#", "mailto:")):
            return m.group(0)
        if url.startswith("images/"):
            new = url
        else:
            new = BLOB_URL + url
        return f'{attr}="{new}"'

    return re.sub(r'(href|src)="([^"]+)"', repl, html)


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    shutil.copytree(ASSETS, OUT / "assets")
    (OUT / "images").mkdir()
    if IMAGE_DIR.is_dir():
        for img in IMAGE_DIR.iterdir():
            if img.suffix.lower() in IMAGE_EXTS:
                shutil.copy2(img, OUT / "images" / img.name)
    (OUT / ".nojekyll").write_text("")

    # ---- index.html: rendered README ----
    readme_html = rewrite_readme_links(md_to_html((ROOT / "README.md").read_text(encoding="utf-8")))
    sections = f"""
<article class="panel">
  <div class="panel-title">Progress Log &middot; README.md</div>
  <div class="md">
{readme_html}
  </div>
</article>
"""
    (OUT / "index.html").write_text(
        render_page(
            title="100 Days of Inference Engineering",
            subtitle="day by day progress log",
            content=sections,
            active="home",
            path="",
            math=True,
        ),
        encoding="utf-8",
    )

    print(f"built 1 page -> {OUT}")


if __name__ == "__main__":
    build()
