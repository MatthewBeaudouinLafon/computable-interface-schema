"""
The Blender(TM) makes analogies between pairwise combinations of a list of specifications.
Currently, this does not include the symmetric pair (ie. if it computes A <=> B, it won't compute B <=> A)
"""

import argparse
import itertools, math
import pprint
import json
import timeit
import yaml
import orjson

import parser
import compiler
import metalgo
import analogylib
from analogylib import Hand

spec_names = [
  'video-editor',
  'calendar',
  'slack',
  'imessage',
  'finder',
  'figma',
  # olli/datanavigator
  # TODO: compare powerpoint with Figma!
]


argp = argparse.ArgumentParser(
                    prog='Belidor Compiler',
                    description='Generates pairwise analogies of a list of UIs')
# argp.add_argument('filenames', action='append')
argp.add_argument('-t', '--timeout', help='Timeout for each analogy.')
argp.add_argument('-v', '--verbose', action="store_true", help='Print incremental results from metalgo.')
argp.add_argument('-o', '--outputfile', help='Where the log file is written.')
argp.add_argument('-c', '--continue', help='File to continue from')  # TODO
argp.add_argument('-d', '--dump', action="store_true", help='Dump results from metalgo to a JSON.')

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

  if (flags.dump):
    with open('json/specs.json', 'wb') as f:
      json_specs = { }
      for spec_name in spec_names:
        with open(spec_name+'.yaml') as spec_f:
          spec_yaml = yaml.safe_load(spec_f)
        json_specs[spec_name] = { "yaml": spec_yaml, "lookup": parser.make_relations(spec_yaml, False)[1] }
      f.write(orjson.dumps(json_specs))

  
  num_combinations = math.comb(len(spec_graphs), 2)
  max_seconds = num_combinations * timeout
  max_minutes, max_seconds = divmod(max_seconds, 60)
  max_hours, max_minutes = divmod(max_minutes, 60)
  print(f'> Making {num_combinations} pairings. It will take at most {max_hours:d}h:{max_minutes:02d}m:{max_seconds:02d}s.')

  json_analogies = []
  
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

    print('\n> Analogy Punchline (unpruned conceptual nodes only):')
    for sinister_node, dexter in analogy[0].items():
      is_conceptual = sinister_graph.nodes[sinister_node]['layer'] == 'conceptual'
      dexter_node, is_pruned = dexter
      if is_conceptual and not is_pruned:
        print(f"{sinister_node:>30} <=> {dexter_node:<30}")

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

    if (flags.dump):
      json_analogies.append( { "inputs": [sinister_name, dexter_name], "analogy": analogy[0]} )

  if (flags.dump):
    with open('json/analogies.json', 'wb') as f:
      f.write(orjson.dumps(json_analogies))

    # break  # DEBUGGING - first pairing only

  print('> Done!')
