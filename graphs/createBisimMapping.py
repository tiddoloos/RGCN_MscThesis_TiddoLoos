import argparse
import csv

from collections import defaultdict
from os import listdir
from typing import Dict, List
import click

"""Run this file from './graphdata/' .
This file creates a mapping of the (k)bisimualition output created with the 
BiSimulation pipeline of Till Blume: https://github.com/t-blume/fluid-spark.
For each folder in <dataset>/bisim/bisimOutput, triples like 'sumNode isSummaryOf orgNode'
are stored in a .nt file in <dataset>/bisim/map/ .
"""

def compare_nodes(orgHash_to_orgNode: dict):
    org_nodes = set()
    with open(f'{dataset}/{dataset}_complete.nt', 'r') as file:
        triples = file.read().splitlines()
        for triple in triples:
            triple_list = triple[:-2].split(" ", maxsplit=2)
            if triple_list != ['']:
                s, p, o = triple_list[0].lower(), triple_list[1].lower(), triple_list[2].lower()
                for i in [s, o]:
                    org_nodes.add(i)
    count = 0
    for _, orgNodes in orgHash_to_orgNode.items():
            for node in orgNodes:
                if node not in org_nodes:
                    count+=1
    if click.confirm(f'{count} mapped (probably literal) nodes do not match with original nodes. If {count} is < 1% of {len(org_nodes)} it probably wont harm performance. Do you want to continue?', default=True):
        return

def reformat(node: str) -> str:
    if dataset != 'AM' and dataset != 'BGS':
        if 'xmlschema' in node:
            split = node.rsplit('^^', 1)
            if len(split) < 2:
                split.insert(0,'""')
                node = '^^<'.join(split) + '>'
                return node
            else:
                lit = '<' + split[1] + '>'
                node = '^^'.join([split[0], lit])
                return node
        if node.startswith('http://informatik.uni-kiel.de/fluid#'):
            node = node.replace('http://informatik.uni-kiel.de/fluid#', '_:')
            return node
        else:
            node = '<' + node + '>'
            return node
    if dataset == 'AM':
        if 'http' in node:
            if node.startswith('http://informatik.uni-kiel.de/fluid#'):
                node = node.replace('http://informatik.uni-kiel.de/fluid#', '_:')
            else:
                node = '<' + node + '>'
            return node
        else:
            return node
    if dataset == 'BGS':
        pass


def csv_to_mapping(path: str, org: bool = True) -> Dict[str, List[str]]:
    mapping: Dict[str, List[str]] = defaultdict(list)
    with open(path, 'rt') as f:
        lines = csv.reader(f, skipinitialspace=False, quotechar=None)
        next(lines)
        for line in lines:
            line = ','.join(line)
            line = line.rsplit(',', 1)
            if org:
                node = reformat(line[0])
                mapping[line[1]].append(node)
            else:
                mapping[line[0]].append(line[1])
    return mapping

def write_to_nt(orgHash_to_orgNode: defaultdict(list), sumNode_to_orgHash: defaultdict(list), map_path: str, k: str) -> None:
    with open(f'{map_path}{k}.nt', 'w') as m:
            for sumNode, orgHashes in sumNode_to_orgHash.items():
                for orgHash in orgHashes:
                    nodes = orgHash_to_orgNode[orgHash]
                    for node in nodes:
                        m.write(f'<{sumNode}> <isSummaryOf> {node} .\n')
    print('Mapping saved')

def create_bisim_map_nt(path: str, map_path: str) -> None:
    dirs = sorted([x for x in listdir(path) if not x.startswith('.')])
    for dir in dirs:
        files = sorted([s for s in listdir(f'{path}/{dir}/') if not s.startswith('.')])
        for file in files:
            if file.startswith('orgNode'):
                orgHash_to_orgNode = csv_to_mapping(f'{path}/{dir}/{file}')
            else:
                sumNode_to_orgHash = csv_to_mapping(f'{path}/{dir}/{file}', org=False)
        
        # compare node from map file with original file
        compare_nodes(orgHash_to_orgNode)

        k = dir.split('_')[-1]
        write_to_nt(orgHash_to_orgNode, sumNode_to_orgHash, map_path, k)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='experiment arguments')
    parser.add_argument('-dataset', type=str, choices=['AIFB', 'AM', 'MUTAG', 'TEST'], help='inidcate dataset name')
    dataset = vars(parser.parse_args())['dataset']

    path = f'./graphs/{dataset}/bisim/bisimOutput'
    map_path = f'./graphs/{dataset}/bisim/map/{dataset}_bisim_map_'

    create_bisim_map_nt(path, map_path)
