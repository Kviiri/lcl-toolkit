#the actual Pycosat-based solver
#input: graph definition, edge constraints
#output: legal node -> label mapping

#input format:
# graph definition
#  - one line per edge
#  - each edge in form (from_id:int, (dir_label:str, to_id_int))
# edge constraints
#  - one line per constraint
#  - each constraint in form (direction, (from_label:int, to_label:int))


import pycosat
import argparse
from ast import literal_eval
from collections import defaultdict
from itertools import product


def main():
    parser=argparse.ArgumentParser('Generate k-tiles for given dimensions.')

    parser.add_argument('graphdef_path', metavar='graph_file', type=str, 
        help='Graph definition file.')

    parser.add_argument('constraints_path', metavar='constraint_file', type=str, 
        help='Constraint file.')

    parser.add_argument('bitcount', metavar = 'bitcount', type=int,
        help='Bits per node label.')

    parser.add_argument('-i', dest = 'invert', action='store_true',
        help='Invert constraints (banned instead of allowed edges.')
    parser.add_argument('-p', dest = 'short_output', action='store_true',
        help='Omit printing the solution, just prints SAT/UNSAT for solved/unsolved problem.')

    parser.add_argument('outfile', metavar='output_path', nargs='?',
        help='the path to output to (omit to print to stdout)')
    
    args = parser.parse_args()
    bitcount = args.bitcount

    #construct the problem constraints
    constraints_by_dir=defaultdict(set)
    with open(args.constraints_path) as f:
        for line in f:
            constraint = literal_eval(line)
            constraints_by_dir[constraint[0]].add(constraint[1])

    if not args.invert:
        constraints_by_dir = invert_constraints(constraints_by_dir, bitcount)

    #construct the graph
    edges_by_node = defaultdict(set)
    with open(args.graphdef_path) as f:
        for line in f:
            edge = literal_eval(line)
            edges_by_node[edge[0]].add(edge[1])

    #clausekey stores the number of the first bit belonging to a given node
    node_clausekey = {}
    current_clausekey = 1
    for node in edges_by_node:
        node_clausekey[node] = current_clausekey
        current_clausekey += bitcount

    clauselist = []
    for from_node in edges_by_node:
        for edge in edges_by_node[from_node]:
            if edge[0] not in constraints_by_dir:
                continue
            for ineligible_pair in constraints_by_dir[edge[0]]:
                newclause = [(node_clausekey[from_node] + i) * (-1 if ineligible_pair[0] >> i & 1 else 1) for i in range(bitcount)] \
                          + [(node_clausekey[edge[1]] + i) * (-1 if ineligible_pair[1] >> i & 1 else 1) for i in range(bitcount)]
                clauselist.append(newclause)

    solution = pycosat.solve(clauselist)
    if args.short_output or solution=="UNSAT":
        print("SAT" if solution!="UNSAT" else "UNSAT")
    else:
        node_labeling = {}
        for node in edges_by_node:
            clausekey = node_clausekey[node]
            label = 0
            for i in range(bitcount):
                if solution[clausekey+i-1] == clausekey+i:
                    label += 2**i
            node_labeling[node] = label
        print(str(node_labeling))

def invert_constraints(constraints_by_dir: dict, bitcount: int):
    all_pairs = {d: set([(l[0], l[1]) for l in product(range(2**bitcount), repeat=2)]) for d in 'NE'}
    ret = {}
    for d in all_pairs:
        ret[d] = [pair for pair in all_pairs[d] if pair not in constraints_by_dir[d]]
    return ret

if __name__ == '__main__':
    main()