"""Planificación del corpus PeruSIL con anotaciones de prueba (sin red ni videos)."""
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
import numpy as np

from src.dataset.dataset_loader import Dataset, split_dataset
from src.dataset.perusil import build_plan, canonical, participant_id, read_annotations, read_table, simulated_split, to_ms

TABLE = ("Nombre Video,Participante,Código de Historia,Historia,Cambio de cuadro,Inicio 1,Final 1,Inicio 2,Final 2,Comentarios\n"
         "Historias vinetas (1),1,1,X,1,0:00,0:10,,,\n"
         "Historias vinetas (2),2,1,X,,,,,,\n"
         "Historias vinetas (3),3,1,X,1,1:50,,,,sin final\n")


def srt(entries):
    blocks = []
    for number, (start, end, label) in enumerate(entries, 1):
        stamp = lambda ms: f"00:{ms // 60000:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
        blocks.append(f"{number}\n{stamp(start)} --> {stamp(end)}\n{label}\n")
    return "\n".join(blocks)


class TestPeruSIL(unittest.TestCase):
    def write_fixture(self, folder):
        table = Path(folder) / "info_videos.tab"
        table.write_text("﻿" + TABLE, encoding="utf-8")
        archive = Path(folder) / "SRT.tar"
        files = {
            "Historias vinetas (1)": [(5000, 5400, "pensar"), (15000, 15400, "Pensar"), (20000, 20500, "Mujer"), (40000, 40400, "qué?")],
            "Historias vinetas (2)": [(3000, 3500, "PENSAR"), (8000, 8300, "mujer")],
            "Historias vinetas (3)": [(4000, 4500, "Pensar"), (30000, 30400, "Mujer"), (115000, 115500, "MUJER")],
        }
        with tarfile.open(archive, "w") as output:
            for name, entries in files.items():
                data = srt(entries).encode("utf-8")
                info = tarfile.TarInfo(f"SRT/SRT_SEGMENTED_SIGN/{name}.srt")
                info.size = len(data)
                output.addfile(info, io.BytesIO(data))
        return read_table(table), read_annotations(archive)

    def test_parsing(self):
        self.assertEqual(to_ms("2:08"), 128000)
        self.assertEqual(canonical(" qué? "), "QUE?")
        with tempfile.TemporaryDirectory() as folder:
            table, segments = self.write_fixture(folder)
        self.assertEqual(table["Historias vinetas (1)"]["excluded_ms"], [(0, 10000)])
        self.assertEqual(table["Historias vinetas (3)"]["excluded_ms"], [(110000, float("inf"))])
        self.assertEqual(len(segments), 9)
        self.assertEqual(segments[0]["gloss"], "PENSAR")

    def test_plan_excludes_camera_motion_and_requires_split_coverage(self):
        with tempfile.TemporaryDirectory() as folder:
            table, segments = self.write_fixture(folder)
        plan = build_plan(table, segments, min_samples=2, min_participants=2, max_classes=5)
        self.assertEqual(plan["discarded"], {"tramo con movimiento de cámara": 2})  # 0:05 en video 1 y 1:55 en video 3
        # Con 3 personas la partición es 1/1/1: solo entran glosas presentes en las tres (QUE? solo la hace p01).
        self.assertEqual(plan["classes"], ["MUJER", "PENSAR"])
        self.assertEqual({clip["participant_id"] for clip in plan["clips"]}, {"perusil-p01", "perusil-p02", "perusil-p03"})
        self.assertNotIn(5000, [clip["start_ms"] for clip in plan["clips"]])
        with self.assertRaises(ValueError):  # Con menos de 2 glosas válidas no hay plan
            build_plan(table, segments, min_samples=2, min_participants=2, exclude={"MUJER"})

    def test_simulated_split_matches_training_split(self):
        people = [participant_id(n) for n in range(1, 18)]
        groups = np.repeat(people, 2)
        dataset = Dataset(np.zeros((len(groups), 30, 126), np.float32), np.tile([0, 1], len(people)), groups,
                          [], [], "x", ["A", "B"])
        expected = split_dataset(dataset)
        simulated = simulated_split(people)
        for name, indices in expected.items():
            self.assertEqual(set(groups[indices]), simulated[name])


if __name__ == "__main__":
    unittest.main()
