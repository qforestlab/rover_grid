import pandas as pd
import numpy as np
import argparse
import os
# import matplotlib.pyplot as plt
import math as m

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

    df = pd.read_csv(csv_path)

    required_columns = {"Easting", "Northing"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        parser.error(f"CSV is missing required column(s): {', '.join(sorted(missing_columns))}")
    if len(df) != 1:
        parser.error(f"CSV must contain exactly one data row; found {len(df)}.")

    row = df.iloc[0]
    coordinates = pd.to_numeric(row[["Easting", "Northing"]], errors="coerce")
    if coordinates.isna().any():
        parser.error("CSV 'Easting' and 'Northing' values must be present and numeric.")

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
    parser.add_argument("-c", "--csv", type=str, required=True)
    parser.add_argument("-g", "--gridsize", type=int, required=True)
    parser.add_argument("-e", "--ew_points", type=int, required=True)
    parser.add_argument("-n", "--ns_points", type=int, required=True)
    parser.add_argument("-a", "--angle", type=float)
    parser.add_argument("--keep_corner", action='store_true')
    parser.add_argument("-o", "--out_file", type=str, default=None)

    args = parser.parse_args()

    if args.angle is None:
        args.angle = 0

    sw_coordinates, df_elevation = check_coordinates_csv(args.csv, parser)

    print(f"Laying out {args.ew_points} points in east-west direction and {args.ns_points} in north-south direction.")
    print(f"Using a gridsize of {args.gridsize} m. and angle of {args.angle} deg. (angle with n-s axis in clockwise direction around sw point)")

    # TODO: change to lat/long so Global CS can be used on the Rover

    coords = sw_corner_to_grid(sw_coordinates, args.gridsize, args.ew_points, args.ns_points, args.angle)

    # DEBUG
    # print(coords)
    # plt.axis('equal')
    # plt.scatter(coords[:,0], coords[:,1])
    # plt.show()

    # add dummy elevation
    elevation_arr = np.ones((len(coords),1)) * df_elevation
    coords_el = np.hstack((coords, elevation_arr))

    df = pd.DataFrame(coords_el, columns=["Easting", "Northing", "Elevation"])
    

    # remove first row as this points has been recorded already
    if not args.keep_corner:
        df = df.iloc[1:]

    df['Name'] = df.index

    if args.out_file is not None:
        df.to_csv(args.out_file, index=False)
    else:
        df.to_csv("grid_generated.csv", index=False)


if __name__ == "__main__":
    main()