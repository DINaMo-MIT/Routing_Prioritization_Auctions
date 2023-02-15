import os
# os.getcwd("../prod_version")

from helpers import *   ## Constants
from agents import *
from grid import *
from envs import *
from simulate import *

import matplotlib.pyplot as plt
from final_plotter import final_plotter

import pickle

outputs = []
for i in range(1, 5):
    temp = None
    # name = "./data/output_" + str(i) + ".pkl"
    name = "./data/fullrun_" + str(i) + ".pkl"
    with open(name, 'rb') as f:
        temp = pickle.load(f)
    
    outputs.append(temp)


scenes = ["Random Scenario", "Bimodal Scenario", "Crossing Scenario", "Hub and Spoke Scenario"]


parameters = {'axes.labelsize': 16,
          'axes.titlesize': 20}
plt.rcParams.update(parameters)

f, axs = plt.subplots(9, len(scenes), figsize=(7.75 * len(scenes), 7.5 * 5), gridspec_kw=dict(height_ratios=[4, 0.25, 4, 1, 4, 1, 4, 1, 4], width_ratios=[1,1,1,1], wspace = 0.22, hspace = 0), dpi=40)

title = True

# hiding the extra column
# , wspace = 0.2, hspace = 0.25 
# axe = axs[:, 0]
# for ax in axe:
#     ax.set_visible(False)
# plotset = [0, 1, 3, 5, 7]

for i in range(len(outputs)):

    final_plotter(outputs[i], axs[:, i], scenario = scenes[i], title=title)
    title=False

if True:
    plt.savefig('full_sim_output.png', bbox_inches='tight')
else:
    plt.show()