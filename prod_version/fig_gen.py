from helpers import *
from agents import *
from grid_cap import *

layout = Layout(layout_pointy, Point(1, 1), Point(0, 0))



grid = Grid(2)

agents = []
agents.append(Agent(Hex(1, -1, 0), Hex(0, 0, 0), 1, 0))

# small cycle
agents.append(Agent(Hex(-1, 0, 1), Hex(-2, 0, 2), 2, 0))
agents.append(Agent(Hex(-2, 0, 2), Hex(-1, -1, 2), 3, 0))
agents.append(Agent(Hex(-1, -1, 2), Hex(-1, 0, 1), 2, 0))

# other conflicts

agents.append(Agent(Hex(0, 2, -2), Hex(0, 0, 0), 4, 0))
agents.append(Agent(Hex(0, 1, -1), Hex(0, 0, 0), 6, 0))
agents.append(Agent(Hex(-1, 2, -1), Hex(0, 0, 0), 2, 0))

agents.append(Agent(Hex(-2, 1, 1), Hex(-2, 0, 2), 2, 0))


# agents[1]._loc = Hex(0, -1, 1)
for i, ag in enumerate(agents):
    ag._id = chr(i + 65)
    ag.move((ag._steps[ag._index], 0))

plot_locations_special(layout, grid.coords_l, agents)