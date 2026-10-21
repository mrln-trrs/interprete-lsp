"""Exporta los tokens de `static/styles.css` (:root) a formato DTCG 2025.10.

La fuente única es el CSS; el JSON se regenera y `--check` falla si quedó desactualizado.
Uso: python -m scripts.export_tokens [--check]
"""
import json
from pathlib import Path
import re
import sys

CSS = Path("static/styles.css")
OUTPUT = Path("docs/design/tokens.dtcg.json")
DECLARATION = re.compile(r"--([a-z0-9-]+)\s*:\s*([^;]+);")


def root_declarations(css_text):
    block = re.search(r":root\s*{([^}]*)}", css_text)
    if not block:
        raise ValueError("styles.css no tiene bloque :root")
    return {name: value.strip() for name, value in DECLARATION.findall(block.group(1))}


def to_token(value, groups):
    alias = re.fullmatch(r"var\(--([a-z0-9-]+)\)", value)
    if alias:
        target = alias.group(1)
        group = next((name for name, members in groups.items() if target in members), None)
        if group is None:
            raise ValueError(f"Alias a token inexistente: {target}")
        return group, {"$value": "{" + f"{group}.{target}" + "}"}
    hex_color = re.fullmatch(r"#([0-9A-Fa-f]{6})", value)
    if hex_color:
        components = [round(int(hex_color.group(1)[i:i + 2], 16) / 255, 4) for i in (0, 2, 4)]
        return "color", {"$type": "color", "$value": {"colorSpace": "srgb", "components": components,
                                                      "hex": "#" + hex_color.group(1).lower()}}
    dimension = re.fullmatch(r"(\d+(?:\.\d+)?)(px|rem)", value)
    if dimension:
        number = float(dimension.group(1))
        return "dimension", {"$type": "dimension",
                             "$value": {"value": int(number) if number.is_integer() else number, "unit": dimension.group(2)}}
    raise ValueError(f"Valor de token no soportado: {value}")


def build(css_text):
    declarations = root_declarations(css_text)
    groups, tokens = {}, {"$description": "Generado desde static/styles.css por scripts/export_tokens.py; no editar a mano."}
    # Primero valores directos y luego alias, para que todo alias apunte a un token ya definido.
    for name, value in sorted(declarations.items(), key=lambda item: item[1].startswith("var(")):
        group, token = to_token(value, groups)
        groups.setdefault(group, set()).add(name)
        tokens.setdefault(group, {})[name] = token
    return tokens


def main(argv):
    rendered = json.dumps(build(CSS.read_text(encoding="utf-8-sig")), ensure_ascii=False, indent=2) + "\n"
    if "--check" in argv:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
            print("tokens.dtcg.json desactualizado: ejecute python -m scripts.export_tokens")
            return 1
        print("tokens.dtcg.json al día")
        return 0
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"Escrito {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
