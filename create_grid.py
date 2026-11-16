import pandas as pd
import numpy as np
import argparse
import logging
import os
import math as m

logger = logging.getLogger(__name__)


def sw_corner_to_grid(easting_northing_sw, grid_size, ew_number_of_pos, ns_number_of_points, angle):
    # get array of points on ew and ns edges
    easting_array = np.arange(easting_northing_sw[0], easting_northing_sw[0] + ew_number_of_pos*grid_size, grid_size)
    northing_array = np.arange(easting_northing_sw[1], easting_northing_sw[1] + ns_number_of_points*grid_size, grid_size)
    # convert edge arrays to coordinate grid
    xv, yv = np.meshgrid(easting_array, northing_array)
    coords = np.array([xv.flatten(), yv.flatten()]).T

    # rotate around sw_point
    # first translate to origin
    coords = coords - easting_northing_sw
    # apply rotation
    c = m.cos(np.deg2rad(angle))
    s = m.sin(np.deg2rad(angle))
    matrix = np.array([[c,s], [-s, c]])
    coords = np.matmul(matrix, coords.T).T
    # translate back
    coords += easting_northing_sw
    return coords


def check_coordinates_csv(csv_path, parser):
    if not os.path.isfile(csv_path):
        parser.error(f"CSV file not found: {csv_path}")

    try:
        df = pd.read_csv(csv_path)
    except (
        OSError,
        UnicodeDecodeError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
    ) as error:
        parser.error(f"Could not read CSV file '{csv_path}': {error}")

    required_columns = {"Easting", "Northing"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        parser.error(f"CSV is missing required column(s): {', '.join(sorted(missing_columns))}")
    if len(df) != 1:
        parser.error(f"CSV must contain exactly one data row; found {len(df)}.")

    row = df.iloc[0]
    coordinates = pd.to_numeric(row[["Easting", "Northing"]], errors="coerce")
    if not np.isfinite(coordinates.to_numpy()).all():
        parser.error("CSV 'Easting' and 'Northing' values must be finite numbers.")

    elevation = row.get("Elevation", 0)
    if pd.isna(elevation):
        elevation = 0
    try:
        elevation = float(elevation)
    except (TypeError, ValueError):
        parser.error("CSV 'Elevation' value must be numeric when provided.")

    return coordinates.to_numpy(), elevation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--csv",
        type=str,
        required=True,
        help="Input CSV with one row containing Easting and Northing in meters.",
    )
    parser.add_argument(
        "-g",
        "--gridsize",
        type=int,
        required=True,
        help="Grid spacing in meters; must be a positive integer.",
    )
    parser.add_argument(
        "-e",
        "--ew_points",
        type=int,
        required=True,
        help="Number of grid points in the east-west direction; must be positive.",
    )
    parser.add_argument(
        "-n",
        "--ns_points",
        type=int,
        required=True,
        help="Number of grid points in the north-south direction; must be positive.",
    )
    parser.add_argument(
        "-a",
        "--angle",
        type=float,
        default=0,
        help="Clockwise rotation in degrees from the north-south axis around the SW corner (default: 0).",
    )
    parser.add_argument(
        "--keep_corner",
        action="store_true",
        help="Include the input SW corner in the generated output (omitted by default).",
    )
    parser.add_argument(
        "-o",
        "--out_file",
        type=str,
        default="grid_generated.csv",
        help="Output CSV path (default: grid_generated.csv).",
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    for option, value in (
        ("--gridsize", args.gridsize),
        ("--ew_points", args.ew_points),
        ("--ns_points", args.ns_points),
    ):
        if value <= 0:
            parser.error(f"{option} must be a positive integer.")

    output_path = args.out_file
    sw_coordinates, df_elevation = check_coordinates_csv(args.csv, parser)

    try:
        same_file = os.path.samefile(args.csv, output_path)
    except FileNotFoundError:
        same_file = os.path.realpath(args.csv) == os.path.realpath(output_path)
    except OSError as error:
        parser.error(f"Could not compare input and output paths: {error}")
    if same_file:
        parser.error("Output file must not be the same as the input CSV.")

    logger.info(
        "Laying out %s points east-west and %s points north-south.",
        args.ew_points,
        args.ns_points,
    )
    logger.info(
        "Using a grid spacing of %s m and a clockwise angle of %s degrees from the north-south axis.",
        args.gridsize,
        args.angle,
    )

    coords = sw_corner_to_grid(sw_coordinates, args.gridsize, args.ew_points, args.ns_points, args.angle)

    # Copy the input elevation to every generated point.
    elevation_arr = np.ones((len(coords),1)) * df_elevation
    coords_el = np.hstack((coords, elevation_arr))

    df = pd.DataFrame(coords_el, columns=["Easting", "Northing", "Elevation"])
    

    # The input corner has already been recorded.
    if not args.keep_corner:
        df = df.iloc[1:]

    df['Name'] = df.index

    df.to_csv(output_path, index=False)
    logger.info("Generated grid saved to %s.", output_path)


if __name__ == "__main__":
    main()