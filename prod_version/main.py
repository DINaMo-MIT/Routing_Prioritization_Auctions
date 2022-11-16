from helpers import *   ## Constants are over here
from agents import *
from grid import *
from envs import *
from simulate import *


## Different scenarios - encapsulated in envs.py
# grid, agents, schedule = create_connected(radius = 3)
# grid size = sum(1 to n) * 6 + 1
# grid, agents, schedule = create_random(num_agents=50, radius = 2, seed = 10)          # small random scenario
grid, agents, schedule = create_random(num_agents=256, radius=7, iters=50, seed=12)     # random scenario
# grid, agents, schedule = create_cycle_testing_cap()                                   # cycle testing
# grid, agents, schedule = create_connected(radius=4)                                   # connected chain of flights
# grid, agents, schedule = create_bimodal(num_agents = 62, time = 50, radius = 3, operator_flag = True)
# grid, agents, schedule = create_crossing(num_agents = [40,60], radius = 7, time = 50, points = 4)
# grid, agents, schedule = create_hubspoke(num_agents = [25, 25, 25, 25, 25, 25], radius = 7, seed = None)
for i, ag in enumerate(agents):
    ag._id = i

    if False:       # for debugging flights
        print("Agent ", ag._id)
        print("Origin \t", ag._origin, "\t Destination \t", ag._dest)
        print("Departure \t", ag._depart_t, "\t Sched.  Arrival \t", ag._schedule_t)

rev, delay, std_delay, _, _, _, _, _, _, _, _, _ = simulate(grid, agents, schedule, vis= False, prior="accrueddelay", output=True, debug=False)
# rev, delay, std_delay, _, _, _, _, _, _, _, _, _ = simulate(grid, agents, schedule, vis= False, prior="backpressure", output=True, debug=False)

# rev, delay, std_delay, _, _, _, _, _, _, _, _, _ = simulate(grid, agents, schedule, vis= True, prior="secondback", output=True, debug=False)


# try case of just a large cycle - only one cycle test case
# fix the calc_backpressure stuff - consider changing code so we skip sectors already covered