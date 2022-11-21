# %%
from helpers import *   ## Constants are over here
from agents import *
from grid import *
from envs import *
from simulate import *

delay_dict = {}
std_delay_dict = {}

for seed in range(10):
    for priority in ['reversals', 'backpressure', 'accrueddelay',]: # 'secondprice', 'secondback']:
        grid, agents, schedule = create_random(num_agents=256, radius=7, iters=50, seed=seed)     # random scenario
        rev, delay, std_delay, _, _, _, _, _, _, _, _, _ = simulate(grid, agents, schedule, vis= False, prior=priority, output=False, debug=False)

        delay_dict[priority] = delay
        std_delay_dict[priority] = std_delay

    print('Seed:', seed)
    print('Total Delay')
    print('backpressure:', delay_dict['backpressure'])
    print('reversals:', delay_dict['reversals'])
    print('accrued delay:', delay_dict['accrueddelay'])

    if delay_dict['backpressure'] > delay_dict['reversals'] or delay_dict['backpressure'] > delay_dict['accrueddelay']:
        print('backpressure not most efficient') 

    print('\n')

# %%
np.mean(delay_dict['backpressure'])
np.mean(delay_dict['reversals'])
np.mean(delay_dict['accrueddelay'])
# %%
