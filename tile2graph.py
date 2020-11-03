#creates a graph from one or two sets of input tiles
#expected input file format: one tile per line: represented by a set of tuples (x, y)
#output format: one edge per line: (a, (dir, b)) where a, b are int codes for tiles, dir in NESW

from ast import literal_eval
from lcl_utils import transpose_tile, tile_to_int
import argparse

def main():
    parser=argparse.ArgumentParser("Combine one or two tile files into a graph file. "
    "If h_file is omitted, v_file is transposed as h_file.")

    parser.add_argument('w', metavar = 'w', type=int, 
        help='Width of output tiles.')

    parser.add_argument('h', metavar = 'h', type=int, 
        help='Height of output tiles.')

    parser.add_argument('v_file', metavar = 'v_file', type=str, 
        help='Tiles representing vertical edges.')

    parser.add_argument('h_file', metavar = 'h_file', type=str, nargs='?', 
        help='Tiles representing horizontal edges (omit to transpose vertical edges).')

    args = parser.parse_args()
    hedges = set()
    if args.h_file:
        with open(args.h_file) as f:
            for line in f.readlines():
                hedges.add(frozenset(one for one in literal_eval(line)))
    else:
        with open(args.v_file) as f:
            for line in f.readlines():
                hedges.add(frozenset(one for one in transpose_tile(literal_eval(line))))
            
    
    vedges = set()
    with open(args.v_file) as f:
        for line in f.readlines():
            vedges.add(frozenset(one for one in literal_eval(line)))
    
    tilewidth = args.w
    tileheight = args.h
    edges = []
    
    for tile in vedges:
        top_tile = set((x,y) for (x,y) in tile if y < tileheight)
        bot_tile = set((x,y-1) for (x,y) in tile if y > 0)
        edges.append(str((tile_to_int(top_tile, tilewidth), ('S', tile_to_int(bot_tile, tilewidth)))))
        edges.append(str((tile_to_int(bot_tile, tilewidth), ('N', tile_to_int(top_tile, tilewidth)))))
    
    
    for tile in hedges:
        west_tile = set((x,y) for (x,y) in tile if x < tilewidth)
        east_tile = set((x-1, y) for (x,y) in tile if x > 0)
        edges.append(str((tile_to_int(west_tile, tilewidth), ('E', tile_to_int(east_tile, tilewidth)))))
        edges.append(str((tile_to_int(east_tile, tilewidth), ('W', tile_to_int(west_tile, tilewidth)))))
    
    for edge in edges:
        print(edge)

if __name__ == '__main__':
    main()