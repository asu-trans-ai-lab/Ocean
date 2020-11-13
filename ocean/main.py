# @author        Jiawei Lu
# @email         jiaweil9@asu.edu
# @create date   2020-04-16 16:27:39
# @desc          [main file]


import initnet
import netgen
from outputnet import *




working_directory = r'C:\Users\Administrator\Desktop\asu\consolidated'

coordinate_type = 'll'                          # m: meter, ll: latlon, f: feet
geometry_source = 'l'                           # n: none, l: link file, g: geomerey file
unit_of_length = 'm'                           # m: meter, km:kilometer, mi: mile, f: feet
segment_unit = 'm'                              # m: meter, km:kilometer, mi: mile, f: feet
speed_unit = 'mph'                              # mph: mile per hour, kph: kilometer per hour

link_type_list = [1,2,3,4,5,6,7]                      # discard link types not in this list
connector_type = -1                             # link type of connetors, -1 if no connector


min_link_length = 3.0                           # meter, links shorter than that will be removed, > 2 * lenght_of_cut[0]
comb_links = False                              # remove 2-degree nodes
auto_connection = True                          # generate movement connections for intersections without predefined movement info
connector_geometry_for_output = 2               # 1: with lane offset; 2: no lane offset

length_of_cell = 7.0
length_of_cut = {0: 1.0, 1: 8.0, 2: 12.0, 3: 14.0, 4: 16.0, 5: 18.0, 6: 20, 7:22, 8:24}  # e.g. 2:8.0 cut 8 meters if the original macro link has 2 lanes, etc
for i in range(9,100): length_of_cut[i] = 25
cells_in_queue_area = 0            # for Signalized Intersections
width_of_lane = 3.5


if __name__ == "__main__":
    macro_net = initnet.CInitNet(working_directory, coordinate_type, geometry_source, unit_of_length, segment_unit, speed_unit,
                                 link_type_list, connector_type,
                                 min_link_length, comb_links, width_of_lane)
    macro_net.readInputData()
    macro_net.initialization()
    net_generator = netgen.CNetGenerator(macro_net, length_of_cell, length_of_cut, width_of_lane, auto_connection, cells_in_queue_area)
    net_generator.generateNet()
    outputNetworks(macro_net, net_generator, connector_geometry_for_output)
