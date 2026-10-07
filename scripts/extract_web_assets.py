"""One-time migration from inline demo assets; uses AST, never imports native vision."""
import ast
from pathlib import Path
import re


def main():
    source = Path("web_server.py")
    text = source.read_text(encoding="utf-8")
    tree = ast.parse(text)
    node = next(node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "_HTML" for target in node.targets))
    html = ast.literal_eval(node.value)
    style = re.search(r"<style>(.*?)</style>", html, re.S)
    script = re.search(r"<script>(.*?)</script>", html, re.S)
    if not style or not script:
        raise ValueError("Assets already migrated or not found")
    Path("static").mkdir(exist_ok=True)
    Path("static/styles.css").write_text(style.group(1).strip() + "\n", encoding="utf-8")
    Path("static/app.js").write_text(script.group(1).strip() + "\n", encoding="utf-8")
    html = html[:script.start()] + '<script src="/static/app.js" defer></script>' + html[script.end():]
    style = re.search(r"<style>(.*?)</style>", html, re.S)
    html = html[:style.start()] + '<link rel="stylesheet" href="/static/styles.css"/>' + html[style.end():]
    lines = text.splitlines(keepends=True)
    replacement = '_HTML = """' + html + '"""\n'
    text = "".join(lines[:node.lineno - 1]) + replacement + "".join(lines[node.end_lineno:])
    source.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
