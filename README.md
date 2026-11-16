# dGNSS grid creation scripts

This repo contains scripts to generate coordinates of a forest plot (scanning) grid, starting from a single corner coordinate (or 2, 3, 4 corners) and user-specified grid size. The output, a csv with coordinates, can be uploaded to e.g. an Emlid Reach rover to stake out positions in the field. Detailed instructions on the entire Emlid workflow can be found in the attached manual or on Teams.

## Installation

If you do not already have the repository, clone it and enter its directory:

```sh
git clone https://github.com/qforestlab/rover_grid.git
cd rover_grid
```

### With Conda

From the repository directory, create the environment from [`environment.yml`](./environment.yml):

```sh
conda env create -f environment.yml
conda activate rover-grid
python create_grid.py --help
```

Activate `rover-grid` again whenever you open a new terminal to work on the scripts. If the dependencies in `environment.yml` change later, update the environment with:

```sh
conda env update -f environment.yml --prune
```

## Using the scripts

1. Export the Rover project to CSV after registering 1, 2, 3, or 4 corners.
2. Run the appropriate grid-generation script below from the activated environment.
3. Import `grid_generated.csv` (or your chosen output filename) into the Rover project.

## Create grid from single (SW) point:

```
python create_grid.py --csv /path/to/csvfile --gridsize GRIDSIZE --ew_points EW_POINTS --ns_points NS_POINTS [--out_file /path/to/outfile] [--angle ANGLE] [--keep_corner] 
```

- -c/--csv: path to a CSV with exactly one data row containing `Easting` and `Northing`; `Elevation` is optional and defaults to 0
- -g/--gridsize: desired grid size in meters
- -e/--ew_points: desired number of points in East/West direction
- -n/--ns_points: desired number of points in North/South direction
- (optional) -a/--angle: angle with NS axis, rotated clockwise around SW corner 
- (optional) --keep_corner: also keeps the first sw point the grid is based on in the new csv file
- (optional) -o/--out_file: path of output file

> NOTE: SW corner is assumed in the script, however it will still work for other corners. Make sure to set ew_points, ns_points and angle accordingly and double check results.


## Create grid from 4 corner points:

```
python create_grid_4_corners.py --csv /path/to/csvfile  --ew_points EW_POINTS --ns_points NS_POINTS [--out_file /path/to/outfile]
```

- -c/--csv: path to exported csv file
- -e/--ew_points: desired number of points in East/West direction
- -n/--ns_points: desired number of points in North/South direction
- (optional) -o/--out_file: path of output file

> NOTE: ew direction is determined automatically as the edge from the most sw corner to the most se corner. If this does not give the desired result, just switch around the ew_points and ns_points args.


## Create grid from 2 corner points:

```
python create_grid_2_corners.py --csv /path/to/csvfile --gridsize GRIDSIZE --n_points_along N_POINTS_ALONG --n_points_projected N_POINTS_PROJECTED [--project_inverse] [--out_file /path/to/outfile]
```

- -c/--csv: path to exported csv file
- -g/--gridsize: desired grid size in meters
- -a/--n_points_along: desired number of points in East/West direction
- -p/--n_points_projected: desired number of points in North/South direction
- (optional) --project_inverse: if set, projects to inverse side 
- (optional) -o/--out_file: path of output file

> NOTE: This method generates the grid by using the two first points as one axis and projecting a second axis pependicular to this edge. Note that the gridsize is only used for the perpendicular edge, the points along the given edge will be spaced equally along the edge. Actual gridsize along this edge will be printed out.

> NOTE: By default, projects to right side of vector from first to second corner. To project to other side, use --project_inverse option.


## Create grid from 3 corner points:

```
python create_grid_3_corners.py --csv /path/to/csvfile --ew_points EW_POINTS --ns_points NS_POINTS [--out_file /path/to/outfile]
```

- -c/--csv: path to exported csv file
- -e/--ew_points: desired number of points in East/West direction
- -n/--ns_points: desired number of points in North/South direction
- (optional) -i/--inner_index: index of inner corner point
- (optional) -o/--out_file: path of output file

> NOTE: This method generates the fourth corner by summing the vectors of both edges, then calls the 4 corner grid generation.

> NOTE: The inner crom from which to project will be determined as the corner with the largest angle in the triangle formed by the 3 corners. In a very parallelogram-shaped plot, this might not give the desired plot, in which case you can give the index (1,2 or 3) of the inner corner point using the -i/--inner_index parameter.