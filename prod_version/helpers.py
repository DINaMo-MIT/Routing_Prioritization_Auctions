from __future__ import division
from __future__ import print_function
import collections
import math
import numpy as np
from scipy.stats import norm, poisson
import heapq as hq
import uuid
from copy import deepcopy

import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon, Arrow, FancyArrow
import matplotlib.lines as lines
import seaborn as sns

# Define constants
CAPACITY = 2

## Hex stuff

Point = collections.namedtuple("Point", ["x", "y"])

_H = collections.namedtuple("Hex", ["q", "r", "s"])
class _Hex(_H):
    def __repr__(self):
        return 'h(' + str(self.q) + ',' + str(self.r) + ',' + str(self.s) + ')'

def Hex(q, r, s):
    assert not (round(q + r + s) != 0), "q + r + s must be 0"
    return _Hex(q, r, s)

def hex_add(a, b):
    return Hex(a.q + b.q, a.r + b.r, a.s + b.s)

def hex_subtract(a, b):
    return Hex(a.q - b.q, a.r - b.r, a.s - b.s)

def hex_scale(a, k):
    return Hex(a.q * k, a.r * k, a.s * k)

def hex_rotate_left(a):
    return Hex(-a.s, -a.q, -a.r)

def hex_rotate_right(a):
    return Hex(-a.r, -a.s, -a.q)

hex_directions = [Hex(1, 0, -1), Hex(1, -1, 0), Hex(0, -1, 1), Hex(-1, 0, 1), Hex(-1, 1, 0), Hex(0, 1, -1)]
def hex_direction(direction):
    return hex_directions[direction]

def hex_neighbor(hex, direction):
    return hex_add(hex, hex_direction(direction))

hex_diagonals = [Hex(2, -1, -1), Hex(1, -2, 1), Hex(-1, -1, 2), Hex(-2, 1, 1), Hex(-1, 2, -1), Hex(1, 1, -2)]
def hex_diagonal_neighbor(hex, direction):
    return hex_add(hex, hex_diagonals[direction])

def hex_length(hex):
    return (abs(hex.q) + abs(hex.r) + abs(hex.s)) // 2

def hex_distance(a, b):
    return hex_length(hex_subtract(a, b))

def hex_round(h):
    qi = int(round(h.q))
    ri = int(round(h.r))
    si = int(round(h.s))
    q_diff = abs(qi - h.q)
    r_diff = abs(ri - h.r)
    s_diff = abs(si - h.s)
    if q_diff > r_diff and q_diff > s_diff:
        qi = -ri - si
    else:
        if r_diff > s_diff:
            ri = -qi - si
        else:
            si = -qi - ri
    return Hex(qi, ri, si)

def hex_lerp(a, b, t):
    return Hex(a.q * (1.0 - t) + b.q * t, a.r * (1.0 - t) + b.r * t, a.s * (1.0 - t) + b.s * t)

def hex_linedraw(a, b):
    N = hex_distance(a, b)
    a_nudge = Hex(a.q + 1e-06, a.r + 1e-06, a.s - 2e-06)
    b_nudge = Hex(b.q + 1e-06, b.r + 1e-06, b.s - 2e-06)
    results = []
    step = 1.0 / max(N, 1)
    for i in range(0, N + 1):
        results.append(hex_round(hex_lerp(a_nudge, b_nudge, step * i)))
    return results

def create_hex_grid(radius):
    """
    Inputs:
        radius: radius of hex grid
    Outputs:
        coords: set of tuples (q,r,s) hex coords
    """
    coords = set()
    for q in range(-radius, radius+1):
        r1 = max(-radius, -q - radius)
        r2 = min(radius, -q + radius)

        for r in range(r1, r2+1):
            coords.add(Hex(q, r, -q-r))
    return coords

## Drawing stuff

Orientation = collections.namedtuple("Orientation", ["f0", "f1", "f2", "f3", "b0", "b1", "b2", "b3", "start_angle"])

Layout = collections.namedtuple("Layout", ["orientation", "size", "origin"])

layout_pointy = Orientation(math.sqrt(3.0), math.sqrt(3.0) / 2.0, 0.0, 3.0 / 2.0, math.sqrt(3.0) / 3.0, -1.0 / 3.0, 0.0, 2.0 / 3.0, 0.5)
layout_flat = Orientation(3.0 / 2.0, 0.0, math.sqrt(3.0) / 2.0, math.sqrt(3.0), 2.0 / 3.0, 0.0, -1.0 / 3.0, math.sqrt(3.0) / 3.0, 0.0)
def hex_to_pixel(layout, h):
    M = layout.orientation
    size = layout.size
    origin = layout.origin
    x = (M.f0 * h.q + M.f1 * h.r) * size.x
    y = (M.f2 * h.q + M.f3 * h.r) * size.y
    return Point(x + origin.x, y + origin.y)

def pixel_to_hex(layout, p):
    M = layout.orientation
    size = layout.size
    origin = layout.origin
    pt = Point((p.x - origin.x) / size.x, (p.y - origin.y) / size.y)
    q = M.b0 * pt.x + M.b1 * pt.y
    r = M.b2 * pt.x + M.b3 * pt.y
    return Hex(q, r, -q - r)

def hex_corner_offset(layout, corner):
    M = layout.orientation
    size = layout.size
    angle = 2.0 * math.pi * (M.start_angle - corner) / 6.0
    return Point(size.x * math.cos(angle), size.y * math.sin(angle))

def polygon_corners(layout, h):
    corners = []
    center = hex_to_pixel(layout, h)
    for i in range(0, 6):
        offset = hex_corner_offset(layout, i)
        corners.append(Point(center.x + offset.x, center.y + offset.y))
    return corners

## Visualization stuff

def plot_locations(layout, coords, active, radius = 5):
    """
    Plot location of agents at the moment. For visualization and debugging
    Inputs:
        layout: Layout object for grid visualization
        coords: list of Hex, coordinates that exists on the grid
        active: list of Agents, all agents active and to be plotted
    Returns:
    """

    locations = {}
    for ag in active:
        locations[ag.loc] = (ag._id, ag.finished, ag.bid[0])
    
    fig, ax = plt.subplots(1, dpi=radius * 25)

    # ax.set(xlim=(-7, 7), ylim=(-7,7))
    
    for h in coords:

        color = None
        if h in locations.keys():
            if locations[h][1]: color = "Green"
            else: color = "Red"
        
        # print(hex_to_pixel(layout, h))
        x, y = hex_to_pixel(layout, h)
        hex = RegularPolygon((x,y), numVertices=6, radius= 1, 
                             orientation=np.radians(0), 
                             facecolor= color, alpha=0.2, edgecolor='k')
        ax.add_patch(hex)
        
        if h in locations.keys() and locations[h][2] is not None:
            x_n, y_n = hex_to_pixel(layout, locations[h][2])
            dx = x_n - x
            dy = y_n - y
            arrow = Arrow(x + dx/4, y + dy/4, dx/2, dy/2, width=0.25)
            ax.add_patch(arrow)
            
        # # Also add a text label
        ax.text(x, y, locations[h][0] if h in locations.keys() else '', ha='center', va='center', fontsize="medium")

    # Also add scatter points in hexagon centres
    # ax.scatter(hcoord, vcoord, c=[c[0].lower() for c in colors], alpha=0.5)
    ax.set_aspect('equal')
    ax.autoscale()
    plt.show()

def plot_locations_2(layout, coords, active, radius = 5):

    agents = {}
    locations = {}
    for ag in active:
        agents[ag._id] = (ag.loc, ag.finished, ag.bid[0])
        
        # build the text box
        if ag.loc not in locations: locations[ag.loc] = []
        text = str(ag._id)
        # check if finished
        if ag.finished: text += "*"
        locations[ag.loc].append(text)

    fig, ax = plt.subplots(1, dpi=radius * 25) # figsize=(radius*3, radius*3))
    # ax.set(xlim=(-7, 7), ylim=(-7,7))

    # draw basic grid first
    for h in coords:

        # print(hex_to_pixel(layout, h))
        x, y = hex_to_pixel(layout, h)
        hex = RegularPolygon((x,y), numVertices=6, radius= 1, 
                             orientation=np.radians(0), 
                             facecolor= None, alpha=0.2, edgecolor='k')
        ax.add_patch(hex)

    # build cells for the relevant sectors
    for _id, info in agents.items():
        if info[0] == -1: continue

        # set color - if done Green, else Red
        if info[1]: color = "Green"
        else: color = "Red"

        # draw the hex
        x, y = hex_to_pixel(layout, info[0])
        hex = RegularPolygon((x,y), numVertices=6, radius= 1, 
                             orientation=np.radians(0), 
                             facecolor= color, alpha=0.2, edgecolor='k')
        ax.add_patch(hex)

        # draw the arrow
        if info[2] is not None:
            x_n, y_n = hex_to_pixel(layout, info[2])
            dx = x_n - x
            dy = y_n - y
            arrow = Arrow(x + dx/4, y + dy/4, dx/2, dy/2, width=0.25)
            ax.add_patch(arrow)
    
    # build the text box
    for loc, text in locations.items():
        if loc == -1: continue
        x, y = hex_to_pixel(layout, loc)

        output = ""
        for ag_text in text:
            output += ag_text + ","

        ax.text(x, y, output[:-1], ha='center', va='center', fontsize="medium")
    
    ax.set_aspect('equal')
    ax.autoscale()
    plt.show()