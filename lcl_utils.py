from functools import reduce

#converts tile (a set of (x, y) coordinates) into an integer
def tile_to_int(tile, width):
    return reduce(lambda x, y: x+y, map(lambda x: 2**(x[0] + x[1]*width), tile), 0)

#converts code (integer) to a width-wide tile
def int_to_tile(code, width):
    ret = set()
    index = 0
    while 2**index <= code:
        if code & (2**index):
            ret.add((index%width, index//width))
        index += 1
    return ret

def transpose_tile(tile):
    return set([(y, x) for (x,y) in tile])