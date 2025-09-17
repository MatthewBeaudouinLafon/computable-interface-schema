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
import networkx as nx
from analogylib import Hand
from joblib import Parallel, delayed

spec_names = [
  'video-editor',
  'calendar',
  'slack',
  'imessage',
  'finder',
  'figma',
  # 'kanban-board',
  'slides',
  'web-browser',
  'code-editor',
  'tabs-pattern',
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

def json_normalize_edges(edges):
  normalized = []
  for [k, v] in edges.items():
    normalized.append({ "from": k, "to": v })

  return normalized

def make_analogy(sinister_name, dexter_name, sinister_graph, dexter_graph, timeout):
  stdout = []
  stdout.append(f'> Pairing: {sinister_name} <=> {dexter_name}')
  
  start_time = timeit.default_timer()
  analogy, iterations = metalgo.compute_analogy(sinister_graph, dexter_graph, timeout=timeout)
  end_time = timeit.default_timer()

  stdout.append('> Result:')
  stdout.append(pprint.pformat(analogy, width=200))
  iterations_time = sum(iterations['times'])  # in seconds
  total_time = end_time - start_time
  stdout.append(f'> Result end (successful-iterations = {iterations_time:.1f}s | total-time = {total_time:.1f}s)')

  punchline = []

  stdout.append('\n> Analogy Punchline (unpruned conceptual nodes only):')

  analogy_graph = analogylib.graph_from_analogy(analogy, side=analogylib.Hand.SINISTER)
  for isolate in nx.connected_components(analogy_graph.to_undirected()):
    added_something = False
    for sinister_node in isolate:
      is_conceptual = sinister_graph.nodes[sinister_node]['layer'] == 'conceptual'
      dexter_node = analogylib.get_analogous_node(analogy, sinister_node)
      is_pruned = analogylib.get_is_pruned(analogy, sinister_node)
      if is_conceptual and not is_pruned:
        added_something = True
        punchline.append([sinister_node, dexter_node])
        stdout.append(f"{sinister_node:>30} <=> {dexter_node:<30}")

    if added_something:
      punchline.append(None)
      stdout.append(f'\n')

  # stdout.append(f'OLD')
  # for sinister_node, dexter in analogy[0].items():
  #   is_conceptual = sinister_graph.nodes[sinister_node]['layer'] == 'conceptual'
  #   dexter_node, is_pruned = dexter
  #   if is_conceptual and not is_pruned:
  #       punchline.append([sinister_node, dexter_node])
  #       stdout.append(f"{sinister_node:>30} <=> {dexter_node:<30}")

  # Note: Cannot print to stdout in multithreaded apps without it being jumbled, so I've set the verbose to False
  # stdout.append('> Itemized Cost:') 
  cost = metalgo.calculate_cost(analogy, sinister_graph, dexter_graph, itemized=True, verbose=False)
  num_analogy_edges = len(analogylib.get_edges(analogy, side=Hand.SINISTER))
  conceptual_connectivity = metalgo.conceptual_connectivity(analogy, sinister_graph)
  score = metalgo.score_analogy(analogy, sinister_graph)

  stdout.append(f'> Summary:')
  stdout.append('num-iterations  : ' + str(len(iterations['times'])))

  stdout.append('cumulative-times: ' + ', '.join([f'{t:.1f}' for t in itertools.accumulate(iterations['times'])]))
  stdout.append('total-cost      : ' + str(cost))
  stdout.append('analogy-edges   : ' + str(num_analogy_edges))
  stdout.append('conceptual-edges: ' + str(conceptual_connectivity))
  stdout.append('score: ' + str(score))
  stdout.append('> Summary end\n')

  dump = { "inputs": [sinister_name, dexter_name], 
            "analogy": [analogy[0], json_normalize_edges(analogy[1])], 
            "cost": cost, 
            "num_analogy_edges": num_analogy_edges,
            "conceptual_connectivity": conceptual_connectivity,
            "punchline": punchline,
            "sinister_graph": nx.node_link_data(sinister_graph, edges="edges"), 
            "dexter_graph": nx.node_link_data(dexter_graph, edges="edges"),
            "score": score,
            "num_iterations": str(len(iterations['times'])),
            "stdout": stdout }

  return "\n".join(stdout), dump
   

if __name__ == '__main__':
  flags = argp.parse_args()
  timeout = 1
  if flags.timeout is not None:
    timeout = int(flags.timeout)

  spec_graphs = {}

  # Import and compile are specs, skipping those that don't work.
  for spec_name in spec_names:
    print('> Importing', spec_name)
    spec_graphs[spec_name] = compiler.compile(spec_name+'.yaml')

  # Write out specs
  with open('json/specs.json', 'wb') as f:
    json_specs = { }
    for spec_name in spec_names:
      spec_yaml = parser.spec_from_file(spec_name+'.yaml')
      # with open(spec_name+'.yaml') as spec_f:
      #   spec_yaml = yaml.safe_load(spec_f)
      json_specs[spec_name] = { "yaml": spec_yaml, "lookup": parser.make_relations(spec_yaml, False)[1] }
    f.write(orjson.dumps(json_specs))

  # Estimate
  num_combinations = math.comb(len(spec_graphs), 2)
  max_seconds = num_combinations * timeout
  max_minutes, max_seconds = divmod(max_seconds, 60)
  max_hours, max_minutes = divmod(max_minutes, 60)
  print(f'> Making {num_combinations} pairings. It will take at most {max_hours:d}h:{max_minutes:02d}m:{max_seconds:02d}s.')

  combinations = list(itertools.combinations(spec_names, 2))

  # Place the smaller graph first
  for i in range(len(combinations)):
    sinister_graph = spec_graphs[combinations[i][0]]
    dexter_graph = spec_graphs[combinations[i][1]]

    if (sinister_graph.size() > dexter_graph.size()):
      combinations[i] = [combinations[i][1], combinations[i][0]]
  
  analogies = Parallel(n_jobs=-1)(delayed(make_analogy)(sinister_name, dexter_name, spec_graphs[sinister_name], spec_graphs[dexter_name], timeout) for sinister_name, dexter_name in combinations)

  stdout = [analogy[0] for analogy in analogies]
  print("\n\n".join(stdout))

  # for sinister_name, dexter_name in combinations:
  #   analogies.append(make_analogy(sinister_name, dexter_name, spec_graphs[sinister_name], spec_graphs[dexter_name], timeout, verbose=flags.verbose))

  with open('json/analogies.json', 'wb') as f:
    f.write(orjson.dumps([analogy[1] for analogy in analogies]))

  print('> Done!')
