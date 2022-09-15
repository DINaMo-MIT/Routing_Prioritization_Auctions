from helpers import *
from agents import *
from grid import *
from envs import *
from simulate import *


## testing  
# grid size = sum(1 to n) * 6 + 1
# grid, agents, schedule = create_random(num_agents=5, radius = 2, seed = 10)
# seed = np.random.randint(1000)
# print(seed)
grid, agents, schedule = create_random(num_agents=124, radius=7, iters=50, seed=12)

# grid, agents, schedule = create_connected(radius=4)
# grid, agents, schedule = create_binomial(num_agents = 62, time = 50, radius = 3)
for i, ag in enumerate(agents):
    ag._id = i
    # ag._var_cost = 5 - i
    # print(ag._steps[0], ag.loc)
#     ag.move((ag._steps[0], 0))
rev, delay, std_delay, _, _ = simulate(grid, agents, schedule, vis= True, prior="secondprice", output=True, debug=False)