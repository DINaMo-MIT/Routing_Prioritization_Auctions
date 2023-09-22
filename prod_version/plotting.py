import os
# os.getcwd("../prod_version")

from helpers import *   ## Constants
from agents import *
from grid import *
from envs import *
from simulate import *

import matplotlib.pyplot as plt
from final_plotter import final_plotter, final_plotter2

import pickle

outputs = []
for i in range(1, 5):
    temp = None
    # name = "./data/output_" + str(i) + ".pkl"
    # name = "./data/fullrun_v3_" + str(i) + ".pkl"
    name = "./data/fullrun_0.9/scenario" + str(i) + ".pkl"
    with open(name, 'rb') as f:
        temp = pickle.load(f)
    
    outputs.append(temp)


scenes = ["Random Scenario", "Bimodal Scenario", "Crossing Scenario", "Hub and Spoke Scenario"]


parameters = {'axes.labelsize': 16,
          'axes.titlesize': 20}
plt.rcParams.update(parameters)

# f, axs = plt.subplots(9, len(scenes), figsize=(7.75 * len(scenes), 7.5 * 5), gridspec_kw=dict(height_ratios=[4, 0.25, 4, 1, 4, 1, 4, 1, 4], width_ratios=[1,1,1,1], wspace = 0.3, hspace = 0), dpi=300)
f, axs = plt.subplots(len(scenes), 5, figsize=(7.5 * 3 + 4.5, 8 * len(scenes)), gridspec_kw=dict(width_ratios=[4, 1.25, 4, 1.25, 4], height_ratios=[1,1,1,1], hspace = 0.3, wspace = 0), dpi=300)
title = True

# hiding the extra column
# , wspace = 0.2, hspace = 0.25 
# axe = axs[:, 0]
# for ax in axe:
#     ax.set_visible(False)
# plotset = [0, 1, 3, 5, 7]

for i in range(len(outputs)):

    # final_plotter(outputs[i], axs[:, i], scenario = scenes[i], title=title)
    final_plotter2(outputs[i], axs[i, :], scenario = scenes[i], title=title)
    title=False

if True:
    # plt.savefig('./presentation work/FiA_work/full_sim_output_0.9_v1.png', bbox_inches='tight')
    plt.savefig('./presentation work/FiA_work/harvest.png', bbox_inches='tight')
else:
    plt.show()