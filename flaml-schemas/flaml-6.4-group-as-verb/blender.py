"""
The Blender(TM) makes analogies between pairwise combinations of a list of specifications.
Currently, this does not include the symmetric pair (ie. if it computes A <=> B, it won't compute B <=> A)
"""

import argparse
import itertools, math
import pprint
import json
import timeit

import compiler
import metalgo
import analogylib
from analogylib import Hand

spec_names = [
  'video-editor',
  'calendar',
  # 'slack',
  # 'finder',
  # 'figma',
  # 'imessage',
  # olli/datanavigator
]


argp = argparse.ArgumentParser(
                    prog='Belidor Compiler',
                    description='Generates pairwise analogies of a list of UIs')
# argp.add_argument('filenames', action='append')
argp.add_argument('-t', '--timeout', help='Timeout for each analogy.')
argp.add_argument('-v', '--verbose', action="store_true", help='Print incremental results from metalgo.')
argp.add_argument('-o', '--outputfile', help='Where the log file is written.')
argp.add_argument('-c', '--continue', help='File to continue from')  # TODO

if __name__ == '__main__':
  flags = argp.parse_args()
  timeout = 60
  if flags.timeout is not None:
    timeout = int(flags.timeout)

  spec_graphs = {}

  # Import and compile are specs, skipping those that don't work.
  for spec_name in spec_names:
    print('> Importing', spec_name)
    spec_graphs[spec_name] = compiler.compile(spec_name+'.yaml')
  
  num_combinations = math.comb(len(spec_graphs), 2)
  max_seconds = num_combinations * timeout
  max_minutes, max_seconds = divmod(max_seconds, 60)
  max_hours, max_minutes = divmod(max_minutes, 60)
  print(f'> Making {num_combinations} pairings. It will take at most {max_hours:d}h:{max_minutes:02d}m:{max_seconds:02d}s.')
  
  for sinister_name, dexter_name in itertools.combinations(spec_names, 2):
  # for sinister_name, dexter_name in itertools.permutations(spec_names, 2): # to make it symmetric ie. A<=>B and B <=> A
    print(f'> Pairing: {sinister_name} <=> {dexter_name}')
    sinister_graph = spec_graphs[sinister_name]
    dexter_graph = spec_graphs[dexter_name]

    start_time = timeit.default_timer()
    analogy, iterations = metalgo.compute_analogy(sinister_graph, dexter_graph, timeout=timeout, verbose=flags.verbose)
    end_time = timeit.default_timer()

    print('> Result:')
    # print(json.dumps(analogy, indent=2))  # doesn't like the tuple key (coward)
    pprint.pprint(analogy, width=200)
    iterations_time = sum(iterations['times'])  # in seconds
    total_time = end_time - start_time
    print(f'> Result end (successful-iterations = {iterations_time:.1f}s | total-time = {total_time:.1f}s)')

    print('> Itemized Cost:')
    cost = metalgo.calculate_cost(analogy, sinister_graph, dexter_graph, itemized=True)
    num_analogy_edges = len(analogylib.get_edges(analogy, side=Hand.SINISTER))
    conceptual_connectivity = metalgo.conceptual_connectivity(analogy, sinister_graph)
    print(f'> Summary:')
    print('num-iterations  :', len(iterations['times']))

    print('cumulative-times:', ', '.join([f'{t:.1f}' for t in itertools.accumulate(iterations['times'])]))
    print('total-cost      :', cost)
    print('analogy-edges   :', num_analogy_edges)
    print('conceptual-edges:', conceptual_connectivity)
    print('> Summary end\n')
    # break  # DEBUGGING - first pairing only

  print('> Done!')
