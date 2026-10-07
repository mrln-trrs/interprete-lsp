import json
from pathlib import Path

TOKENS = {"surface": "#111827", "primary": "#FFFFFF", "secondary": "#D1D5DB",
          "accent": "#A7F3D0", "accent-secondary": "#93C5FD", "warning": "#FDE68A", "danger": "#FECACA"}


def luminance(value):
    channels = [int(value[position:position + 2], 16) / 255 for position in (1, 3, 5)]
    channels = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055)**2.4 for channel in channels]
    return sum(weight * channel for weight, channel in zip((0.2126, 0.7152, 0.0722), channels))


def main():
    background = luminance(TOKENS["surface"])
    ratios = {name: (max(luminance(value), background) + 0.05) / (min(luminance(value), background) + 0.05)
              for name, value in TOKENS.items() if name != "surface"}
    report = {"surface": TOKENS["surface"], "tokens": TOKENS, "contrast_ratios": ratios,
              "all_text_pairs_at_least_7": all(value >= 7 for value in ratios.values())}
    Path("docs/design/CONTRAST-REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(ratios))
    if not report["all_text_pairs_at_least_7"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
