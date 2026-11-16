import argparse
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from create_grid import check_coordinates_csv, sw_corner_to_grid


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "create_grid.py"


class GridCoordinatesTests(unittest.TestCase):
    def test_unrotated_grid_has_expected_spacing_and_order(self):
        coords = sw_corner_to_grid(np.array([100.0, 200.0]), 2, 2, 2, 0)

        np.testing.assert_allclose(
            coords,
            [
                [100.0, 200.0],
                [102.0, 200.0],
                [100.0, 202.0],
                [102.0, 202.0],
            ],
        )

    def test_rotation_keeps_southwest_corner_fixed(self):
        coords = sw_corner_to_grid(np.array([100.0, 200.0]), 2, 2, 2, 90)

        np.testing.assert_allclose(
            coords,
            [
                [100.0, 200.0],
                [100.0, 198.0],
                [102.0, 200.0],
                [102.0, 198.0],
            ],
            atol=1e-12,
        )


class CoordinateCsvTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.csv_path = Path(self.temp_dir.name) / "coordinates.csv"

    def check_csv_error(self, contents, expected_message):
        self.csv_path.write_text(contents)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
            check_coordinates_csv(str(self.csv_path), argparse.ArgumentParser())

        self.assertEqual(error.exception.code, 2)
        self.assertIn(expected_message, stderr.getvalue())

    def test_reads_coordinates_and_defaults_missing_elevation_to_zero(self):
        self.csv_path.write_text("Easting,Northing,Other\n100.5,-200.25,ignored\n")

        coordinates, elevation = check_coordinates_csv(
            str(self.csv_path), argparse.ArgumentParser()
        )

        np.testing.assert_allclose(coordinates, [100.5, -200.25])
        self.assertEqual(elevation, 0)

    def test_blank_elevation_defaults_to_zero(self):
        self.csv_path.write_text("Easting,Northing,Elevation\n100,200,\n")

        _, elevation = check_coordinates_csv(
            str(self.csv_path), argparse.ArgumentParser()
        )

        self.assertEqual(elevation, 0)

    def test_rejects_missing_coordinate_columns(self):
        self.check_csv_error("Elevation\n0\n", "missing required column")

    def test_rejects_non_finite_coordinates(self):
        self.check_csv_error("Easting,Northing\nNaN,200\n", "finite numbers")

    def test_rejects_multiple_data_rows(self):
        self.check_csv_error(
            "Easting,Northing\n100,200\n101,201\n", "exactly one data row"
        )

    def test_reports_empty_csv_read_error(self):
        self.check_csv_error("", "Could not read CSV file")

    def test_reports_malformed_csv_read_error(self):
        self.check_csv_error(
            "Easting,Northing\n100,200\n101,201,300\n", "Could not read CSV file"
        )


class GridCliTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.csv_path = self.root / "coordinates.csv"
        self.csv_path.write_text("Easting,Northing,Elevation\n100,200,5\n")
        self.output_path = self.root / "grid.csv"

    def run_script(self, *extra_args, output_path, cwd=None):
        command = [
            sys.executable,
            str(SCRIPT_PATH),
            "--csv",
            str(self.csv_path),
            "--gridsize",
            "2",
            "--ew_points",
            "2",
            "--ns_points",
            "2",
        ]
        if output_path is not None:
            command.extend(["--out_file", str(output_path)])
        command.extend(extra_args)
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            cwd=cwd,
        )

    def test_writes_expected_grid_and_omits_starting_corner_by_default(self):
        result = self.run_script(output_path=self.output_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        output = pd.read_csv(self.output_path)
        self.assertEqual(list(output.columns), ["Easting", "Northing", "Elevation", "Name"])
        self.assertEqual(len(output), 3)
        self.assertEqual(set(output["Elevation"]), {5.0})
        self.assertNotIn((100.0, 200.0), set(zip(output["Easting"], output["Northing"])))

    def test_keep_corner_includes_starting_corner(self):
        result = self.run_script("--keep_corner", output_path=self.output_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        output = pd.read_csv(self.output_path)
        self.assertEqual(len(output), 4)
        self.assertEqual((output.iloc[0]["Easting"], output.iloc[0]["Northing"]), (100, 200))

    def test_rejects_non_positive_grid_arguments(self):
        result = self.run_script("--gridsize", "0", output_path=self.output_path)

        self.assertEqual(result.returncode, 2)
        self.assertIn("--gridsize must be a positive integer", result.stderr)

    def test_rejects_output_path_same_as_input(self):
        original_contents = self.csv_path.read_text()

        result = self.run_script(output_path=self.csv_path)

        self.assertEqual(result.returncode, 2)
        self.assertIn("Output file must not be the same as the input CSV", result.stderr)
        self.assertEqual(self.csv_path.read_text(), original_contents)

    def test_rejects_default_output_path_same_as_input(self):
        self.csv_path = self.root / "grid_generated.csv"
        self.csv_path.write_text("Easting,Northing,Elevation\n100,200,5\n")
        original_contents = self.csv_path.read_text()

        result = self.run_script(output_path=None, cwd=self.root)

        self.assertEqual(result.returncode, 2)
        self.assertIn("Output file must not be the same as the input CSV", result.stderr)
        self.assertEqual(self.csv_path.read_text(), original_contents)


if __name__ == "__main__":
    unittest.main()
