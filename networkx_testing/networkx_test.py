# %%
import networkx as nx
import pickle
import os
from helpers import *
from functools import reduce

# %%

edges = [(0, 0), (0, 1), (0, 2), (1, 2), (2, 0), (2, 1), (2, 2)]
G = nx.DiGraph(edges)
sorted(nx.simple_cycles(G))

# %%
print('23')
with open('layout.pickle', 'rb') as handle:
    layout = pickle.load(handle)

with open('grid_coords.pickle', 'rb') as handle:
    grid_coords = pickle.load(handle)

with open('active.pickle', 'rb') as handle:
    active = pickle.load(handle)
# %%
plot_locations_2(layout, grid_coords, active, radius = 7)
# %%
# create list of edges
printAgents = False

edges = []
for agent in active:
    if printAgents:
        print(agent.loc)
        print(agent.bid[0])
    edges.append((agent.loc, agent.bid[0]))

print('Create G with {} edges'.format(len(edges)))

# %%
G = nx.DiGraph(edges)
cycles = sorted(nx.simple_cycles(G))
# %%
# find cycles
agent_ids_in_cycles = []
print('Identified {} cycles'.format(len(cycles)))
for c in cycles:
    if printAgents:
        print('\n', c)
    for loc in c:
        if printAgents:
            print(vehicle._id, vehicle.loc, vehicle.bid[0])
        vehicle = [x for x in active if x.loc == loc and x.bid[0] in c][0]
        agent_ids_in_cycles.append(vehicle._id)

print('Found {} vehicles in cycles'.format(reduce(lambda count, l: count + len(l), cycles, 0)))

# %%
# plot cycles
agents_in_cycles = []
for agent in active:
    if agent._id in agent_ids_in_cycles:
        agents_in_cycles.append(agent)

plot_locations_2(layout, grid_coords, agents_in_cycles, radius = 7)


# %%
# remove edges in cycles

# create list of edges
edges_no_cycles = []
for agent in active:
    # print(agent.loc)
    # print(agent.bid[0])
    if agent not in agents_in_cycles:
        edges_no_cycles.append((agent.loc, agent.bid[0]))

# %%
# find longest chain in DAG
G = nx.DiGraph(edges_no_cycles)
cycles = sorted(nx.simple_cycles(G))
print('Identified {} cycles'.format(len(cycles)))

nx.dag_longest_path(G)

# %%
"""
0-->1
|   |
3<--2
3<--2
|   |
4-->5
"""


edges = [(0, 1), (1, 2), (2, 3), (3, 0), (2, 3), (3, 4), (4, 5), (5,2)]
G = nx.DiGraph(edges)
sorted(nx.simple_cycles(G))
nx.dag_longest_path(G)
# %%
