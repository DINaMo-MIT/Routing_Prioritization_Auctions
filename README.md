# Routing_Prioritization_Auctions
 
All code is in `\prod_version`. 

Main function for simulation is in `grid_cap.py`, under the `step_sim` function. New prioritization methods should be written into `class GridCap` and called in `step_sim` by feeding the appropriate prioritization method in `main.py`.

Capacity is set using the `CAPACITY` gloabal at the top of `helpers.py`.

Run `main.py` to test different environments