# lcl-toolkit
A collection of tools for working with Locally Checkable Labeling problems and algorithm synthesis for them.

The toolkit is designed for Python 3, and requires pycosat.

## generate_tiles.py
Creates k-tiles of dimensions w × h. Each k-tile a Python set of tuples representing coordinates (int, int) such that when interpreted as a 4-regular grid G, the nodes indicated by the tuples can appear in the MIS of G<sup>k</sup>.

## tile2graph.py
Taking one or two files containing k-tiles as input, as well as the desired width and height, creates a neighborhood graph of the k-tiles contained. If only one file is provided, it is assumed to be vertical (h = w+1) and is transposed to form the horizontal tiles.

## lcl_utils.py
A collection of miscellaneous helper functions used by the other programs.

## solver.py
Solves a given LCL problem for a given graph. Outputs the solution as a string representation of a Python dict.