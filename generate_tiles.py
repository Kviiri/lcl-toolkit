from itertools import product
from ast import literal_eval
import pycosat
import argparse

def main():
    parser=argparse.ArgumentParser('Generate k-tiles for given dimensions.')

    parser.add_argument('k', metavar = 'k', type=int, 
        help='k (min manhattan distance between anchors)')

    parser.add_argument('w', metavar = 'w', type=int, 
        help='Width of k-tile.')

    parser.add_argument('h', metavar = 'h', type=int, 
        help='Height of k-tile.')

    parser.add_argument('outfile', metavar='output_path', nargs='?',
        help='the path to output to (omit to print to stdout)')
    
    args = parser.parse_args()
    tilewidth = args.w
    tileheight = args.h
    k = args.k
    output = args.outfile

    columnset = create_columns(tileheight, k)
    i = 1
    #initialize tiles as the set of 1×h tiles
    tiles = [(frozenset((0,i) for i in column), 1) for column in columnset]
    
    finished_tiles = []
    
    while tiles:
        cur_tile = tiles.pop()
        new_tiles = extend_valid(cur_tile[0], columnset, cur_tile[1]+1, tileheight, tilewidth, k)
        if cur_tile[1]+1 == tilewidth:
            for tile in new_tiles:
                finished_tiles.append(tile)
        else:
            tiles.extend([(ones, cur_tile[1]+1) for ones in new_tiles])

    valid_tiles=[]
    for tile in finished_tiles:
        if cnfsat_verify(tile, tilewidth, tileheight, k) != None:
            valid_tiles.append(set(tile))

    if output:
        with open(output, "w") as f:
            for tile in valid_tiles:
                f.write(str(tile)+"\n") 


def create_columns(n, k):
    #valid: set of sets of tuples representing valid columns
    #empty column is always valid
    valid = {frozenset()}
    #we start with empty column as a possibility
    old = {frozenset()}
    for number_of_ones in range(1, -(-n//(k+1))+1):
        new = set()
        #try to expand each old tile
        for col in old:
            #in each possible i
            accepted_post = set() 
            accepted_pre = set()
            l = 0
            for i in range(0, n):
                if i not in col and l == 0:
                    accepted_post.update(col, {i})
                elif i in col:
                    l = k
                else:
                    l = l - 1
            l = 0
            for i in reversed(range(0, n)):
                if i not in col and l == 0:
                    accepted_pre.update(col, {i})
                elif i in col == 1:
                    l = k
                else:
                    l = l - 1
            #add successful lines to new if they're not there yet
            new.update(map(lambda x: frozenset(col.union({x})), accepted_pre.intersection(accepted_post)))
        valid.update(new)
        old = new
    return valid

def extend_valid(oneSet, candidate_columns, tilewidth, tileheight, max_width, k):
    candidate_columns = frozenset(frozenset((tilewidth-1, x) for x in y) for y in candidate_columns)
    valid_columns = set() 
    #0: can be 0 or 1
    #1: can only be 1
    #-1: can't be 1
    roweligibilities = [0]*tileheight
    #mark mandatory zeroes -1
    for one in oneSet:
        if one[0] >= tilewidth - 1 - k:
            i = 0
            bypassed = False
            while i < tileheight:
                #todo: optimize if needed
                if is_manhattan_close(one, (tilewidth-1, i), k):
                    bypassed = True
                    roweligibilities[i] = -1
                elif bypassed:
                    break
                i = i + 1
    if tilewidth-2*k > 0:
        #next we add the nondominated zeroes if the tile has any
        #contains (x, y) of all nondominated zeroes
        nondominated_candidates = set((tilewidth-1-k, y) for y in range(k, tileheight-k))
        for one in oneSet:
            delete_set = set()
            #only ones close enough to the edge to count
            if(one[0] >= tilewidth - 2*k - 1):
                for nondom in nondominated_candidates:
                    if is_manhattan_close(nondom, one, k):
                        delete_set.add(nondom)
            nondominated_candidates -= delete_set
            if not nondominated_candidates:
                break
        for nondom in nondominated_candidates:
            roweligibilities[nondom[1]] = 1
    for column in candidate_columns:
        is_valid = True
        for row in range(0, tileheight):
            if roweligibilities[row] == -1 and (tilewidth-1, row) in column:
                is_valid = False
                break
            if roweligibilities[row] == 1 and (tilewidth-1, row) not in column:
                is_valid = False
                break
        if is_valid:
            valid_columns.add(column)
    if not valid_columns:
        return set()

    valid_tiles = map(lambda x: oneSet.union(x), valid_columns)
    return valid_tiles

def get_nondominated_zeroes(tile, tilewidth, tileheight, max_width, k):
    #find non-dominated zeroes at most k away from the edge
    #we ignore the right edge until close to the final size
    nondominated_zeroes = {c for c in product(range(0, tilewidth), range(0, tileheight))}
    nondominated_zeroes = filter(lambda c: not inside_area(c, k, k, max_width-k, tileheight-k), nondominated_zeroes)
    for one in tile:
        nondominated_zeroes = set(filter(lambda nondom: not is_manhattan_close(nondom, one, k), nondominated_zeroes))
        if not nondominated_zeroes:
            break
    return nondominated_zeroes

def get_manhattan(point, k):
    return set(filter(lambda c: is_manhattan_close(c, point, k),
        product(range(point[0] - k, point[0] + k + 1), range(point[1] - k, point[1] + k + 1))))

def is_manhattan_close(point1, point2, k):
    return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1]) <= k

#returns if point (a, b) is within a area defined by x, y, width, height
def inside_area(point, x, y, width, height):
    return point[0] >= x and point[0] < width and point[1] >= y and point[1] < height

#For each non-dominated zero, returns a map from the zero to all eligible ones to satisfy it
def nondominated_zero_neighborhoods(tilewidth, tileheight, nondominated_zeroes, k, exclusionset):
    ret = {}
    for zero in nondominated_zeroes:
        ret[zero] = set(filter(lambda c: not inside_area(c, 0, 0, tilewidth, tileheight),
            get_manhattan(zero, k)))
    return ret

#Creates a set for excluding k-neighbors of existing ones
def get_exclusionset(ones, tilewidth, tileheight, k):
    exclusionset = set()
    for one in ones:
        exclusionset.update(filter(lambda c: not inside_area(c, 0, 0, tilewidth, tileheight),
            get_manhattan(one, k)))
    return exclusionset

#verifies the external satisfiability of a k-tile by CNFSAT.
#returns the tile ("ones") if valid, None otherwise
def cnfsat_verify(ones, tilewidth, tileheight, k):
    nondominated_zeroes = set(
        get_nondominated_zeroes(ones, tilewidth, tileheight, tilewidth, k)
    )
    if not nondominated_zeroes:
        return ones
    exclusionset = get_exclusionset(ones, tilewidth, tileheight, k)
    neighborhoods = nondominated_zero_neighborhoods(
        tilewidth, tileheight, nondominated_zeroes, k, exclusionset)
    neighborhoods = sorted([(a, b - exclusionset) for a, b in neighborhoods.items()],
        key=lambda x: len(x[1]))
    for zero in neighborhoods:
        if not zero[1]:
            return None
    external_node_id = 1
    external_node_map = {}
    for external_node in set.union(*[neighborhood[1] for neighborhood in neighborhoods]):
        external_node_map[external_node] = external_node_id
        external_node_id += 1
    #now all nodes that appear in any neighborhood have a unique integer id 1, 2, ...
    clauselist = []
    handled_nodes = set()
    for neighborhood in neighborhoods:
        #one of the node's external k-neighbors must be true
        clauselist.append([external_node_map[node] for node in neighborhood[1]])
        for external_node in neighborhood[1]:
            if external_node in handled_nodes:
                continue
            external_node_id = external_node_map[external_node]
            handled_nodes.add(external_node)
            for other_external in filter(
              lambda other: is_manhattan_close(external_node, other, k), external_node_map.keys()):
                if external_node != other_external and other_external not in handled_nodes:
                    clauselist.append([-external_node_id, -external_node_map[other_external]])
            handled_nodes.add(external_node)
    if pycosat.solve(clauselist) != 'UNSAT':
        #SOLVED!
        return ones
    else:
        return None

if __name__ == "__main__":
    main()