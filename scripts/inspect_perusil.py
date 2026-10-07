"""Inspect licensed annotations without extracting archives or loading pickle."""
import argparse
from collections import Counter
import hashlib
import json
import re
import tarfile
import unicodedata
from pathlib import Path
from config.actions import ACTIONS


def canonical(value):
    value = "".join(char for char in unicodedata.normalize("NFD", value.upper()) if not unicodedata.combining(char))
    return re.sub(r"\s+", "_", value.strip())


def inspect(archive):
    counts = Counter()
    eligible = Counter()
    files = 0
    with tarfile.open(archive) as source:
        for member in source.getmembers():
            if not member.isfile() or "SRT_SEGMENTED_SIGN/" not in member.name or not member.name.endswith(".srt"):
                continue
            if member.size > 1024 * 1024:
                raise ValueError("Annotation file exceeds inspection budget")
            files += 1
            text = source.extractfile(member).read().decode("utf-8-sig")
            for block in re.split(r"\r?\n\s*\r?\n", text.strip()):
                lines = block.splitlines()
                timestamp_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
                if timestamp_index is not None:
                    label = canonical(" ".join(lines[timestamp_index + 1:]))
                    if label:
                        counts[label] += 1
                        times = re.findall(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})", lines[timestamp_index])
                        if len(times) == 2:
                            start, end = [int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms) for h, m, s, ms in times]
                            if end - start >= 1000:
                                eligible[label] += 1
    return {"source": "PUCP-DGI156 / PeruSIL", "license": "CC0-1.0", "annotation_files": files,
            "archive_sha256": hashlib.sha256(Path(archive).read_bytes()).hexdigest(),
            "exact_vocabulary_matches": {gloss: counts[gloss] for gloss in ACTIONS},
            "one_second_annotation_matches": {gloss: eligible[gloss] for gloss in ACTIONS},
            "distinct_labels": len(counts), "top_labels": counts.most_common(30),
            "limitation": "Exact textual annotation matches only; not isolated validated samples or class correctness."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=Path("data/raw_videos/perusil/SRT.tar"))
    parser.add_argument("--output", type=Path, default=Path("docs/data/PERUSIL-COVERAGE.json"))
    args = parser.parse_args()
    result = inspect(args.archive)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["exact_vocabulary_matches"]))


if __name__ == "__main__":
    main()
