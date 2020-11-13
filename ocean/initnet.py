# @author        Jiawei Lu
# @email         jiaweil9@asu.edu
# @create date   2020-04-16 16:29:15
# @desc          [description]


import pandas as pd
import os
from exitprogram import *
import re
import numpy as np
from coordconvertor import Convertor


class CNode:
    def __init__(self):
        self.name = ''
        self.node_id = 0
        self.x_coord = 0.0
        self.y_coord = 0.0
        self.lat = 0.0
        self.lon = 0.0
        self.zone_id = None
        self.node_seq_no = 0
        self.control_type = ''
        self.m_outgoing_link_list = []
        self.m_incoming_link_list = []

        self.valid = True
        self.is_centroid = True
        self.centroid_meso_node = None

        self.main_node_id = None
        self.new_node = None        # create a new macro node for main node

        self.movement_link_needed = True

        self.x_coord_original_type = 0.0
        self.y_coord_original_type = 0.0

        self.number_of_expanded_mesonode = 0

        self.activity_type = ''
        self.is_boundary = False



class CLink:
    def __init__(self):
        self.name = ''
        self.link_id = ''
        self.link_seq_no = 0
        self.link_key = ''
        self.from_node_id = 0
        self.to_node_id = 0
        self.from_node = None
        self.to_node = None
        self.link_type = 0
        self.TMC = ''
        self.is_connector = False
        self.link_geom_id = 0
        self.dir_flag = 0
        self.lane_cap = 0
        self.speed_limit = 0
        self.number_of_lanes = 0
        self.length = 0.0
        self.geometry_str = ''
        self.orignal_geometry_tuple = ()
        self.geometry_list = []             # geometry after offset
        self.coord_length = 0.0             # length after offset
        self.segment_no_list = []
        self.max_number_of_lanes = 0
        self.breakpoint_list = []
        self.number_of_lanes_list = []
        self.lanes_change_list = []

        self.cutted_number_of_sections = 0
        self.cutted_length = 0.0
        self.cutted_length_in_km = 0.0
        self.cutted_geometry_list = []      # for each section
        self.cutted_breakpoint_list = []
        self.cutted_number_of_lanes_list = []
        self.cutted_lanes_change_list = []

        # no movement link is needed when a unsignalized node only has a incoming link or a outgoing link
        self.upstream_short_cut = False         # no movement needed at upstream
        self.upstream_is_target = False         # connect with other links while keeping its upstream unchanged
        self.downstream_short_cut = False       # no movement needed at downstream
        self.downstream_is_target = False       # connect with other links while keeping its upstream unchanged
        self.length_of_short_cut = 0.1

        self.length_of_cut_upstream = 0.0
        self.length_of_cut_downstream = 0.0

        self.meso_link_id_list = []
        self.valid = True

        self.need_offset = False
        self.geometry_list_original_type = []
        self.mvmt_id_list = []

    def cutLink(self):
        self.cutted_length = self.coord_length - self.length_of_cut_upstream - self.length_of_cut_downstream
        self.cutted_breakpoint_list = self.breakpoint_list.copy()
        self.cutted_number_of_lanes_list = self.number_of_lanes_list.copy()
        self.cutted_lanes_change_list = self.lanes_change_list.copy()

        # if self.link_id == '146777_AB':
        #     a = 1

        for i in range(1, len(self.cutted_breakpoint_list)):
            if self.cutted_breakpoint_list[i] > self.length_of_cut_upstream: break
        del self.cutted_breakpoint_list[0:i]
        self.cutted_breakpoint_list.insert(0, self.length_of_cut_upstream)
        del self.cutted_number_of_lanes_list[0:i - 1]
        del self.cutted_lanes_change_list[0:i - 1]

        for i in range(len(self.cutted_breakpoint_list) - 2, -1, -1):
            if self.coord_length - self.cutted_breakpoint_list[i] > self.length_of_cut_downstream: break
        del self.cutted_breakpoint_list[i + 1:]
        self.cutted_breakpoint_list.append(self.coord_length - self.length_of_cut_downstream)
        del self.cutted_number_of_lanes_list[i + 1:]
        del self.cutted_lanes_change_list[i + 1:]

        self.cutted_number_of_sections = len(self.cutted_number_of_lanes_list)

        last_point_location = 0
        last_point_coord = self.geometry_list[0]
        current_geometry_segment_seq_no = 0
        cutted_geometry_list_temp = []

        for point_no, point_location in enumerate(self.cutted_breakpoint_list):
            geometry_points_before_breakpoint_list = []
            need_length = point_location - last_point_location
            next_break_point_coord = self.geometry_list[current_geometry_segment_seq_no+1]
            remaining_length = ((next_break_point_coord[0] - last_point_coord[0])**2 + (next_break_point_coord[1] - last_point_coord[1])**2)**0.5

            while need_length - remaining_length > 1e-3:
                need_length -= remaining_length
                current_geometry_segment_seq_no += 1
                last_point_coord = self.geometry_list[current_geometry_segment_seq_no]
                next_break_point_coord = self.geometry_list[current_geometry_segment_seq_no+1]
                remaining_length = ((next_break_point_coord[0] - last_point_coord[0])**2 + (next_break_point_coord[1] - last_point_coord[1])**2)**0.5
                geometry_points_before_breakpoint_list.append(last_point_coord)

            delta_x = (next_break_point_coord[0] - last_point_coord[0]) / remaining_length * need_length
            delta_y = (next_break_point_coord[1] - last_point_coord[1]) / remaining_length * need_length
            new_x = last_point_coord[0] + delta_x
            new_y = last_point_coord[1] + delta_y
            geometry_points_before_breakpoint_list.append((new_x,new_y))

            cutted_geometry_list_temp.append(geometry_points_before_breakpoint_list)
            last_point_location = point_location
            last_point_coord = (new_x,new_y)

        for i in range(len(self.cutted_breakpoint_list)-1):
            self.cutted_geometry_list.append([cutted_geometry_list_temp[i][-1]]+cutted_geometry_list_temp[i+1])

    def Initialization(self):
        self.cutLink()


class CMovement:
    def __init__(self):
        self.movement_id = 0
        self.node_id = 0
        self.name = ''
        self.ib_link_id = ''
        self.ib_lane = None
        self.ob_link_id = ''
        self.ob_lane = None
        self.movement_str = ''


class CSegment:
    def __init__(self):
        self.segment_id = 0
        self.segment_no = 0
        self.road_link_id = ''
        self.ref_node_id = 0
        self.start_lr = 0.0
        self.end_lr = 0.0
        self.lane_cap = 0
        self.speed_limit = 0
        self.bike_facility = None
        self.ped_facility = None
        self.parking = None
        self.allowed_uses = None
        self.l_lanes_added = 0
        self.r_lanes_added = 0


class CGeometry:
    def __init__(self):
        self.geom_id = 0
        self.geom_no = 0
        self.name = ''
        self.geometry_str = ''
        self.geometry_list = []

    def generateGeometryList(self):
        try:
            coord_str = re.findall(r'LINESTRING [(](.*?)[)]', self.geometry_str)[0]
        except IndexError:
            print('unsupported geometry format. please use LINESTRING (x1 y1,x2 y2,x3 y3)')
            exitProgram()
        coord_str_list = coord_str.split(',')
        geometry_list_temp = []
        for item in coord_str_list:
            coord_temp = item.split()
            geometry_list_temp.append(tuple(map(float, coord_temp)))

        geometry_list_temp_set = list(set(geometry_list_temp))
        if len(geometry_list_temp_set) != len(geometry_list_temp):
            self.geometry_list = sorted(geometry_list_temp_set, key=geometry_list_temp.index)
        else:
            self.geometry_list = geometry_list_temp


# class CMainNode:
#     def __init__(self):
#         self.main_node_id = 0
#         self.main_node_seq_no = 0
#         self.macro_node_list = []
#         self.new_macro_node = None
#         self.control_type = 0


class CInitNet:
    def __init__(self, working_directory, coordinate_type, geometry_source, unit_of_length, segment_unit, speed_unit, link_type_list, connector_type, min_link_length, comb_links, width_of_lane):
        self.working_directory = working_directory
        self.coordinate_type = coordinate_type
        self.geometry_source = geometry_source
        self.unit_of_length = unit_of_length
        self.segment_unit = segment_unit
        self.speed_unit = speed_unit
        self.width_of_lane = width_of_lane

        self.link_type_list = link_type_list
        self.connector_type = connector_type

        self.min_link_length = min_link_length
        self.comb_links = comb_links

        self.TMC_flag = False

        self.coord_convertor = None

        self.number_of_nodes = 0
        self.number_of_links = 0
        self.number_of_movements = 0
        self.number_of_segments = 0
        self.number_of_geometries = 0

        self.max_node_id = 0
        self.number_of_combined_links = 0

        self.node_list = []
        self.link_list = []
        self.movement_list = []
        self.segment_list = []
        self.geometry_list = []

        self.short_link_list = []

        self.node_id_to_seq_no_dict = {}
        self.link_id_to_seq_no_dict = {}
        self.geometry_id_to_seq_no_dict = {}
        self.movement_id_to_seq_no_dict = {}
        self.link_key_to_seq_no_dict = {}

        self.main_node_id_to_subnode_list_dict = {}     # to original subnodes
        # self.main_node_id_to_node_dict = {}          # to the new created node
        self.main_node_control_type_dict = {}

    def readInputData(self):
        print('Reading input data...')
        # --------------------Node----------------------#
        print('  reading node.csv')
        node_data = pd.read_csv(os.path.join(self.working_directory,'node.csv'))
        self.number_of_nodes = len(node_data)
        coord_list = []

        for i in range(self.number_of_nodes):
            node = CNode()
            try:
                node.node_id = int(node_data.loc[i,'node_id'])
                name = node_data.loc[i,'name']
                node.name = name if not np.isnan(name) else ''
                x_coord = node_data.loc[i,'x_coord']
                y_coord = node_data.loc[i,'y_coord']
                zone_id = node_data.loc[i, 'zone_id']
                if not np.isnan(zone_id): node.zone_id = int(zone_id)

                control_type = node_data.loc[i, 'ctrl_type']
                node.control_type = int(control_type) if not np.isnan(control_type) else 0

                node.activity_type = node_data.loc[i, 'activity_type']
                is_boundary = node_data.loc[i, 'is_boundary']
                if is_boundary == 1: node.is_boundary = True

                if self.coordinate_type == 'm':
                    node.x_coord, node.y_coord = x_coord, y_coord
                elif self.coordinate_type == 'll':
                    node.lat, node.lon = y_coord, x_coord
                    coord_list.append([y_coord, x_coord])
                elif self.coordinate_type == 'f':
                    node.x_coord, node.y_coord = x_coord * 0.3048, y_coord * 0.3048
                else:
                    print('coordinate_type must be chosen from m,ll,f')
                    exitProgram()

                main_node_id = node_data.loc[i,'main_node_id']
                if not np.isnan(main_node_id):
                    node.main_node_id = main_node_id
                    if main_node_id in self.main_node_id_to_subnode_list_dict.keys():
                        if self.main_node_control_type_dict[main_node_id] != node.control_type:
                            print('Different control types detected at main node {}'.format(main_node_id))
                            exitProgram()
                        self.main_node_id_to_subnode_list_dict[main_node_id].append(node)
                    else:
                        self.main_node_id_to_subnode_list_dict[main_node_id] = [node]
                        self.main_node_control_type_dict[main_node_id] = node.control_type

            except KeyError as e:
                print(f'Cannot find {e.args[0]} in the node.csv. Press Enter key to exit')
                exitProgram()

            node.node_seq_no = i
            self.node_list.append(node)
            self.node_id_to_seq_no_dict[node.node_id] = node.node_seq_no
            if node.node_id > self.max_node_id: self.max_node_id = node.node_id

        if self.coordinate_type == 'll':
            coord_array = np.array(coord_list)
            lat_central, lon_central = coord_array[:,0].mean(), coord_array[:,1].mean()
            self.coord_convertor = Convertor(lat_central, lon_central)
            utm_x, utm_y = self.coord_convertor.from_latlon(coord_array[:,0], coord_array[:,1])
            for node_seq_no, node in enumerate(self.node_list):
                node.x_coord, node.y_coord = utm_x[node_seq_no], utm_y[node_seq_no]

        for main_node_id, subnode_list in self.main_node_id_to_subnode_list_dict.items():
            if len(subnode_list) == 1: continue
            node = CNode()
            node.node_id = self.max_node_id + 1
            node.node_seq_no = self.number_of_nodes
            node.x_coord = sum([subnode.x_coord for subnode in subnode_list]) / len(subnode_list)
            node.y_coord = sum([subnode.y_coord for subnode in subnode_list]) / len(subnode_list)
            node.control_type = self.main_node_control_type_dict[main_node_id]
            node.main_node_id = main_node_id
            self.node_list.append(node)

            self.node_id_to_seq_no_dict[node.node_id] = node.node_seq_no
            # self.main_node_id_to_node_dict[main_node_id] = node
            for subnode in subnode_list: subnode.new_node = node
            self.max_node_id += 1
            self.number_of_nodes += 1

        # ---------------------Link-----------------------#
        print('  reading link.csv')
        link_data = pd.read_csv(os.path.join(self.working_directory,'link.csv'), encoding='gb18030')
        self.number_of_links = 0

        if 'TMC' in link_data.columns: self.TMC_flag = True

        for i in range(len(link_data)):
            link = CLink()
            try:
                link.link_type = link_data.loc[i,'link_type']
                if link.link_type not in self.link_type_list: continue
                if link.link_type == self.connector_type: link.is_connector = True

                link.link_id = link_data.loc[i,'link_id']

                from_node_id = int(link_data.loc[i,'from_node_id'])
                from_node = self.node_list[self.node_id_to_seq_no_dict[from_node_id]]
                if from_node.new_node is not None: from_node = from_node.new_node
                link.from_node_id = from_node.node_id
                link.from_node = from_node
                to_node_id = int(link_data.loc[i,'to_node_id'])
                to_node = self.node_list[self.node_id_to_seq_no_dict[to_node_id]]
                if to_node.new_node is not None: to_node = to_node.new_node
                link.to_node_id = to_node.node_id
                link.to_node = to_node
                if link.from_node_id == link.to_node_id: continue

                if self.geometry_source == 'n':
                    # none
                    pass
                elif self.geometry_source == 'l':
                    # link file
                    link.geometry_str = link_data.loc[i,'geometry']
                else:
                    # geometry file
                    link.link_geom_id = int(link_data.loc[i,'link_geom_id'])
                    link.dir_flag = int(link_data.loc[i,'dir_flag'])
                link.lane_cap = float(link_data.loc[i,'capacity'])
                speed_limit = float(link_data.loc[i,'free_speed'])
                if self.speed_unit == 'mph':
                    link.speed_limit = speed_limit * 1.60934
                elif self.speed_unit == 'kph':
                    link.speed_limit = speed_limit
                else:
                    print('speed_unit must be chosen from mph, kph')
                    exitProgram()

                link.number_of_lanes = int(link_data.loc[i,'lanes'])
                if link.number_of_lanes < 1:
                    print(f'number of lanes of link {link.link_id} is invalid')
                    exitProgram()

                link_length = float(link_data.loc[i,'length'])
                if self.unit_of_length == 'm':
                    link.length = link_length
                elif self.unit_of_length == 'km':
                    link.length = link_length * 1000
                elif self.unit_of_length == 'mi':
                    link.length = link_length * 1609.34
                elif self.unit_of_length == 'f':
                    link.length = link_length * 0.3048
                else:
                    print('unit_of_length must be chosen from m,km,mi,f')
                    exitProgram()
                if self.TMC_flag:
                    TMC = link_data.loc[i,'TMC']
                    if TMC == TMC: link.TMC = TMC


            except KeyError as e:
                print('Cannot find {} in the link.csv. Press Enter key to exit'.format(e.args[0]))
                exitProgram()

            link.coordinate_type = self.coordinate_type
            link.link_seq_no = self.number_of_links
            link.link_key = '{}_{}'.format(link.from_node_id,link.to_node_id)
            # link.from_node = self.node_list[self.node_id_to_seq_no_dict[link.from_node_id]]
            link.from_node.m_outgoing_link_list.append(link.link_id)
            # link.to_node = self.node_list[self.node_id_to_seq_no_dict[link.to_node_id]]
            link.to_node.m_incoming_link_list.append(link.link_id)

            self.link_list.append(link)
            self.link_id_to_seq_no_dict[link.link_id] = link.link_seq_no
            self.link_key_to_seq_no_dict[link.link_key] = link.link_seq_no
            self.number_of_links += 1

            if not link.is_connector:
                link.from_node.is_centroid = False
                link.to_node.is_centroid = False

        # remove unreachable nodes
        for node in self.node_list:
            if (len(node.m_incoming_link_list) == 0) and (len(node.m_outgoing_link_list) == 0):
                node.valid = False

        # ------------------Movement--------------------#
        movement_file = os.path.join(self.working_directory,'movement.csv')
        if os.path.isfile(movement_file):
            print('  reading movement.csv')
            movement_data = pd.read_csv(movement_file)
            movement_data = movement_data.astype({'ib_lane':'str', 'ob_lane':'str'})

            for i in range(len(movement_data)):
                mvmt = CMovement()
                try:
                    mvmt.movement_id = int(movement_data.loc[i,'mvmt_id'])
                    # mvmt.node_id = int(movement_data.loc[i,'node_id'])
                    mvmt.ib_link_id = movement_data.loc[i,'ib_link_id']
                    mvmt.ib_lane = movement_data.loc[i,'ib_lane']
                    mvmt.ob_link_id = movement_data.loc[i,'ob_link_id']
                    mvmt.ob_lane = movement_data.loc[i,'ob_lane']
                    mvmt.movement_str = movement_data.loc[i,'movement_str']
                except KeyError as e:
                    print('Cannot find {} in the movement.csv. Press Enter key to exit'.format(e.args[0]))
                    exitProgram()

                if mvmt.ib_link_id not in self.link_id_to_seq_no_dict.keys():
                    print('  warning: ib_link of moevement {} does not exit, movement info will be discarded'.format(mvmt.movement_id))
                    continue
                if mvmt.ob_link_id not in self.link_id_to_seq_no_dict.keys():
                    print('  warning: ob_link of moevement {} does not exit, movement info will be discarded'.format(mvmt.movement_id))
                    continue

                self.movement_list.append(mvmt)
                self.movement_id_to_seq_no_dict[mvmt.movement_id] = self.number_of_movements
                self.number_of_movements += 1
                self.link_list[self.link_id_to_seq_no_dict[mvmt.ib_link_id]].mvmt_id_list.append(mvmt.movement_id)


        # identify nodes do not need movements
        for node in self.node_list:
            if node.main_node_id is not None: continue
            if node.control_type not in [0,1]: continue
            if not node.valid: continue

            # TO DO: centroid node

            if len(node.m_incoming_link_list) == 1 and len(node.m_outgoing_link_list) >= 1:
                # one imcoming link
                ib_link = self.link_list[self.link_id_to_seq_no_dict[node.m_incoming_link_list[0]]]
                ob_link_id_set = set()
                multiple_connection = False
                for mvmt_id in ib_link.mvmt_id_list:
                    mvmt = self.movement_list[self.movement_id_to_seq_no_dict[mvmt_id]]
                    if mvmt.ob_link_id in ob_link_id_set:
                        multiple_connection = True
                        break
                    else:
                        ob_link_id_set.add(mvmt.ob_link_id)
                if multiple_connection: continue

                node.movement_link_needed = False
                ib_link.downstream_short_cut = True
                ib_link.downstream_is_target = True
                for ob_link_id in node.m_outgoing_link_list:
                    ob_link = self.link_list[self.link_id_to_seq_no_dict[ob_link_id]]
                    ob_link.upstream_short_cut = True
            elif len(node.m_outgoing_link_list) == 1 and len(node.m_incoming_link_list) >= 1:
                # one outgoing link
                multiple_connection = False
                for ib_link_id in node.m_incoming_link_list:
                    ib_link = self.link_list[self.link_id_to_seq_no_dict[ib_link_id]]
                    if len(ib_link.mvmt_id_list) > 1:
                        multiple_connection = True
                        break
                if multiple_connection: continue

                node.movement_link_needed = False
                ob_link = self.link_list[self.link_id_to_seq_no_dict[node.m_outgoing_link_list[0]]]
                ob_link.upstream_short_cut = True
                ob_link.upstream_is_target = True
                for ib_link_id in node.m_incoming_link_list:
                    ib_link = self.link_list[self.link_id_to_seq_no_dict[ib_link_id]]
                    ib_link.downstream_short_cut = True


        # ------------------Segment--------------------#
        segment_file = os.path.join(self.working_directory,'segment.csv')
        if os.path.isfile(segment_file):
            print('  reading segment.csv')
            segment_data = pd.read_csv(os.path.join(self.working_directory,'segment.csv'))

            for i in range(len(segment_data)):
                segment = CSegment()
                try:
                    segment.segment_id = int(segment_data.loc[i,'segment_id'])
                    segment.road_link_id = segment_data.loc[i,'road_link_id']
                    segment.ref_node_id = int(segment_data.loc[i,'ref_node_id'])
                    start_lr, end_lr = float(segment_data.loc[i,'start_lr']), float(segment_data.loc[i,'end_lr'])

                    if self.segment_unit == 'm':
                        segment.start_lr, segment.end_lr = start_lr, end_lr
                    elif self.segment_unit == 'km':
                        segment.start_lr, segment.end_lr = start_lr * 1000, end_lr * 1000
                    elif self.segment_unit == 'mi':
                        segment.start_lr, segment.end_lr = start_lr * 1609.34, end_lr * 1609.34
                    elif self.segment_unit == 'f':
                        segment.start_lr, segment.end_lr = start_lr * 0.3048, end_lr * 0.3048
                    else:
                        print('segment_unit must be chosen from m,km,mi,f')
                        exitProgram()

                    segment.lane_cap = float(segment_data.loc[i,'capacity'])
                    segment.speed_limit = segment_data.loc[i,'free_speed']
                    segment.l_lanes_added = int(segment_data.loc[i,'l_lanes_added'])
                    segment.r_lanes_added = int(segment_data.loc[i,'r_lanes_added'])
                except KeyError:
                    print('Please check field names in segment.csv. Press Enter key to exit')
                    exitProgram()

                if segment.road_link_id not in self.link_id_to_seq_no_dict.keys():
                    print('  warning: link of segment {} does not exit, segment info will be discarded'.format(segment.segment_id))
                    continue

                segment.segment_no = self.number_of_segments
                self.link_list[self.link_id_to_seq_no_dict[segment.road_link_id]].segment_no_list.append(segment.segment_no)
                self.number_of_segments += 1
                self.segment_list.append(segment)

        # ------------------Geometry--------------------#
        if self.geometry_source == 'g':
            print('  reading link_geometry.csv')
            geometry_data = pd.read_csv(os.path.join(self.working_directory,'link_geometry.csv'))
            self.number_of_geometries = len(geometry_data)

            for i in range(self.number_of_geometries):
                geom = CGeometry()
                try:
                    geom.geom_id = int(geometry_data.loc[i,'link_geom_id'])
                    geom.geometry_str = geometry_data.loc[i,'geometry']
                except KeyError as e:
                    print('Cannot find {} in the link_geometry.csv. Press Enter key to exit'.format(e.args[0]))
                    exitProgram()

                geom.geom_no = i
                geom.generateGeometryList()
                self.geometry_list.append(geom)
                self.geometry_id_to_seq_no_dict[geom.geom_id] = geom.geom_no


    def initialization(self):
        # ------------------splitSegments--------------#
        for link in self.link_list:
            accuracy = 2.0
            breakpoint_list_temp = [0, link.length]

            if link.length <= accuracy:
                link.breakpoint_list = breakpoint_list_temp.copy()
            else:
                for segment_no in link.segment_no_list:
                    segment = self.segment_list[segment_no]
                    if segment.ref_node_id == link.from_node_id:
                        breakpoint_list_temp.append(max(0, segment.start_lr))
                        breakpoint_list_temp.append(min(link.length, segment.end_lr))

                while breakpoint_list_temp:
                    target_point = breakpoint_list_temp[0]
                    remove_list = []
                    for item in breakpoint_list_temp:
                        if target_point - accuracy <= item <= target_point + accuracy:
                            remove_list.append(item)
                    link.breakpoint_list.append(target_point)
                    for item in remove_list: breakpoint_list_temp.remove(item)
                link.breakpoint_list.sort()

            for i in range(len(link.breakpoint_list) - 1):
                link.number_of_lanes_list.append(link.number_of_lanes)
                link.lanes_change_list.append([0, 0])
                from_point = link.breakpoint_list[i]
                to_point = link.breakpoint_list[i + 1]
                for segment_no in link.segment_no_list:
                    segment = self.segment_list[segment_no]
                    if (from_point - accuracy <= max(0, segment.start_lr) <= from_point + accuracy) and (
                            to_point - accuracy <= min(link.length, segment.end_lr) <= to_point + accuracy):
                        link.number_of_lanes_list[-1] += (segment.l_lanes_added + segment.r_lanes_added)
                        link.lanes_change_list[-1][0] += segment.l_lanes_added
                        link.lanes_change_list[-1][1] += segment.r_lanes_added

            link.max_number_of_lanes = max(link.number_of_lanes_list)

        # ------------------obtainGeometry--------------#
        original_geometry_to_link_dict = {}
        for link in self.link_list:
            if self.geometry_source == 'n':
                from_node = self.node_list[self.node_id_to_seq_no_dict[link.from_node_id]]
                to_node = self.node_list[self.node_id_to_seq_no_dict[link.to_node_id]]
                link.original_geometry_tuple = ((from_node.x_coord, from_node.y_coord), (to_node.x_coord, to_node.y_coord))
            elif self.geometry_source == 'g':
                original_geometry_list = self.geometry_list[self.geometry_id_to_seq_no_dict[link.link_geom_id]].geometry_list.copy()
                if link.dir_flag == -1: original_geometry_list.reverse()

                if self.coordinate_type == 'm':
                    pass
                elif self.coordinate_type == 'll':
                    original_geometry_list_temp = []
                    for item in original_geometry_list:
                        x, y = self.coord_convertor.from_latlon(item[1], item[0])
                        original_geometry_list_temp.append((x, y))
                    original_geometry_list = original_geometry_list_temp
                elif self.coordinate_type == 'f':
                    original_geometry_list = [tuple(0.3048 * x for x in item) for item in original_geometry_list]
                else:
                    print('coordinate_type must be chosen from m,ll,f')
                    exitProgram()
                link.original_geometry_tuple = tuple(original_geometry_list)
            elif self.geometry_source == 'l':
                if ('<LineString><coordinates>' not in link.geometry_str) and ('LINESTRING (' not in link.geometry_str):
                    print('check geometry format in link file')
                    exitProgram()

                geometry_list_temp = []
                if '<LineString><coordinates>' in link.geometry_str:
                    coord_str = re.findall(r'<LineString><coordinates>(.*)</coordinates></LineString>', link.geometry_str)[0]
                    coord_str_list = coord_str.split(' ')
                    for item in coord_str_list:
                        coord_temp = item.split(',')[:2]
                        geometry_list_temp.append(tuple(map(float, coord_temp)))
                else:
                    coord_str = re.findall(r'LINESTRING [(](.*?)[)]', link.geometry_str)[0]
                    coord_str_list = coord_str.split(', ')
                    for item in coord_str_list:
                        coord_temp = item.split(' ')[:2]
                        geometry_list_temp.append(tuple(map(float, coord_temp)))

                geometry_list_temp_set = list(set(geometry_list_temp))
                if len(geometry_list_temp_set) != len(geometry_list_temp):
                    # geometry_list = geometry_list_temp_set.sort(key=geometry_list_temp.index)
                    geometry_list = sorted(geometry_list_temp_set,key=geometry_list_temp.index)
                else:
                    geometry_list = geometry_list_temp

                if self.coordinate_type == 'm':
                    link.original_geometry_tuple = tuple(geometry_list)
                elif self.coordinate_type == 'll':
                    geometry_list_temp = []
                    for item in geometry_list:
                        x, y = self.coord_convertor.from_latlon(item[1], item[0])
                        geometry_list_temp.append((x, y))
                    link.original_geometry_tuple = tuple(geometry_list_temp)
                elif self.coordinate_type == 'f':
                    link.original_geometry_tuple = (tuple(0.3048 * x for x in item) for item in geometry_list)
                else:
                    print('coordinate_type must be chosen from m,ll,f')
                    exitProgram()
            original_geometry_to_link_dict[link.original_geometry_tuple] = link
            reverse_geometry_tuple = link.original_geometry_tuple[::-1]
            if reverse_geometry_tuple in original_geometry_to_link_dict.keys():
                original_geometry_to_link_dict[reverse_geometry_tuple].need_offset = True
                link.need_offset = True

        for link in self.link_list:
            if link.need_offset:
                line_offset = (link.max_number_of_lanes / 2 + 0.5) * self.width_of_lane
                offset_coord_list_temp = []  # ((start_x,start_y), (end_x, end_y))

                for i in range(len(link.original_geometry_tuple) - 1):
                    start_x = link.original_geometry_tuple[i][0]
                    start_y = link.original_geometry_tuple[i][1]
                    end_x = link.original_geometry_tuple[i + 1][0]
                    end_y = link.original_geometry_tuple[i + 1][1]

                    delta_x = end_x - start_x
                    delta_y = end_y - start_y
                    length = (delta_x ** 2 + delta_y ** 2) ** 0.5
                    offset_x = delta_y / length * line_offset
                    offset_y = -1 * delta_x / length * line_offset

                    offset_coord_list_temp.append(((start_x + offset_x, start_y + offset_y), (end_x + offset_x, end_y + offset_y)))

                link.geometry_list = [offset_coord_list_temp[0][0]]
                for i in range(len(offset_coord_list_temp) - 1):
                    uf = offset_coord_list_temp[i][0]
                    ut = offset_coord_list_temp[i][1]
                    df = offset_coord_list_temp[i + 1][0]
                    dt = offset_coord_list_temp[i + 1][1]
                    if ut == df:
                        link.geometry_list.append(ut)
                    else:
                        A = [[ut[1] - uf[1], uf[0] - ut[0]], [dt[1] - df[1], df[0] - dt[0]]]
                        b = [(ut[1] - uf[1]) * uf[0] - (ut[0] - uf[0]) * uf[1],
                             (dt[1] - df[1]) * df[0] - (dt[0] - df[0]) * df[1]]
                        A_mat = np.mat(A)
                        b_mat = np.mat(b).T
                        solution = np.linalg.inv(A_mat) * b_mat
                        x, y = solution[0, 0], solution[1, 0]
                        link.geometry_list.append((x, y))
                link.geometry_list.append(offset_coord_list_temp[-1][1])
            else:
                link.geometry_list = list(link.original_geometry_tuple)

            for i in range(len(link.geometry_list) - 1):
                link.coord_length += ((link.geometry_list[i + 1][0] - link.geometry_list[i][0]) ** 2 + (link.geometry_list[i + 1][1] - link.geometry_list[i][1]) ** 2) ** 0.5
            if abs(link.coord_length - link.length) / link.length > 0.2:
                print('  warning: link id: {}, link length inconsistency detected. link length {}, coordinate length {}'.format(link.link_id, link.length, link.coord_length))
            link.breakpoint_list = [item / link.length * link.coord_length for item in link.breakpoint_list]

            if link.coord_length < self.min_link_length:
                self.short_link_list.append(link)

        # ================= remove short links ===============#
        if self.short_link_list: print('  removing links shorter than {} meters'.format(self.min_link_length))
        number_of_removed_links = 0
        for link in self.short_link_list:
            if not link.valid: continue

            link.valid = False
            from_node = link.from_node
            to_node = link.to_node
            from_node.valid = False
            to_node.valid = False

            number_of_removed_links += 1

            reverse_link_key = '{}_{}'.format(link.to_node_id, link.from_node_id)
            if reverse_link_key in self.link_key_to_seq_no_dict.keys():
                reverse_link = self.link_list[self.link_key_to_seq_no_dict[reverse_link_key]]
                reverse_link.valid = False
                number_of_removed_links += 1

            node = CNode()
            node.node_id = self.max_node_id + 1
            node.x_coord = (from_node.x_coord + to_node.x_coord) * 0.5
            node.y_coord = (from_node.y_coord + to_node.y_coord) * 0.5
            node.node_seq_no = self.number_of_nodes

            # node.m_outgoing_link_list = from_node.m_outgoing_link_list + to_node.m_outgoing_link_list
            # node.m_incoming_link_list = from_node.m_incoming_link_list + to_node.m_incoming_link_list

            if (from_node.zone_id != -1) and (to_node.zone_id != -1):
                print('    warning: from node and to node of short link {} both have associated traffic zones, only from node zone is kept'.format(link.link_id))
                node.zone_id = from_node.zone_id
            elif (from_node.zone_id != -1) and (to_node.zone_id == -1):
                node.zone_id = from_node.zone_id
            elif (from_node.zone_id == -1) and (to_node.zone_id != -1):
                node.zone_id = to_node.zone_id

            for link_id in from_node.m_outgoing_link_list:
                link2 = self.link_list[self.link_id_to_seq_no_dict[link_id]]
                if link2.valid:
                    node.m_outgoing_link_list.append(link_id)
                    link2.from_node = node
                    link2.from_node_id = node.node_id
            for link_id in from_node.m_incoming_link_list:
                link2 = self.link_list[self.link_id_to_seq_no_dict[link_id]]
                if link2.valid:
                    node.m_incoming_link_list.append(link_id)
                    link2.to_node = node
                    link2.to_node_id = node.node_id
            for link_id in to_node.m_outgoing_link_list:
                link2 = self.link_list[self.link_id_to_seq_no_dict[link_id]]
                if link2.valid:
                    node.m_outgoing_link_list.append(link_id)
                    link2.from_node = node
                    link2.from_node_id = node.node_id
            for link_id in to_node.m_incoming_link_list:
                link2 = self.link_list[self.link_id_to_seq_no_dict[link_id]]
                if link2.valid:
                    node.m_incoming_link_list.append(link_id)
                    link2.to_node = node
                    link2.to_node_id = node.node_id

            self.node_list.append(node)
            self.node_id_to_seq_no_dict[node.node_id] = node.node_seq_no
            self.number_of_nodes += 1
            self.max_node_id += 1
        if self.short_link_list: print('  {} short links have been removed'.format(number_of_removed_links))

        # ================= combine adjacent links ===============#
        if self.comb_links:
            print('  combing adjacent links')
            for node in self.node_list:
                if (len(node.m_outgoing_link_list) != 1) or (len(node.m_incoming_link_list) != 1) or (not node.valid):
                    continue

                ib_link = self.link_list[self.link_id_to_seq_no_dict[node.m_incoming_link_list[0]]]
                ob_link = self.link_list[self.link_id_to_seq_no_dict[node.m_outgoing_link_list[0]]]

                # if ib_link.number_of_lanes != ob_link.number_of_lanes: continue

                node.valid = False
                ib_link.valid = False
                ob_link.valid = False

                link = CLink()


                link.name = ib_link.name
                link.link_id = 'L{}'.format(self.number_of_combined_links)
                link.link_seq_no = self.number_of_links
                link.from_node_id = ib_link.from_node_id
                link.to_node_id = ob_link.to_node_id
                link.link_key = '{}_{}'.format(link.from_node_id, link.to_node_id)
                link.from_node = ib_link.from_node
                link.to_node = ob_link.to_node
                link.link_geom_id = 0
                link.dir_flag = 0
                link.lane_cap = (ib_link.coord_length * ib_link.lane_cap + ob_link.coord_length * ob_link.lane_cap) / (ib_link.coord_length + ob_link.coord_length)
                link.speed_limit = (ib_link.coord_length * ib_link.speed_limit + ob_link.coord_length * ob_link.speed_limit) / (ib_link.coord_length + ob_link.coord_length)
                link.number_of_lanes = ib_link.number_of_lanes

                link.geometry_str = ''

                ib_geometry_x, ib_geometry_y = ib_link.geometry_list[-1]
                ob_geometry_x, ob_geometry_y = ob_link.geometry_list[0]
                new_geometry_x = 0.5 * (ib_geometry_x + ob_geometry_x)
                new_geometry_y = 0.5 * (ib_geometry_y + ob_geometry_y)
                new_ib_link_geometry_list = ib_link.geometry_list[:-1] + [(new_geometry_x, new_geometry_y)]
                new_ob_link_geometry_list = [(new_geometry_x, new_geometry_y)] + ib_link.geometry_list[1:]
                link.geometry_list = ib_link.geometry_list[:-1] + [(new_geometry_x, new_geometry_y)] + ib_link.geometry_list[1:]        # geometry after offset

                new_ib_link_coord_length = 0.0
                for i in range(len(new_ib_link_geometry_list)-1):
                    new_ib_link_coord_length += ((new_ib_link_geometry_list[i + 1][0] - new_ib_link_geometry_list[i][0]) ** 2 + (new_ib_link_geometry_list[i + 1][1] - new_ib_link_geometry_list[i][1]) ** 2) ** 0.5
                new_ob_link_coord_length = 0.0
                for i in range(len(new_ob_link_geometry_list)-1):
                    new_ob_link_coord_length += ((new_ob_link_geometry_list[i + 1][0] - new_ob_link_geometry_list[i][0]) ** 2 + (new_ob_link_geometry_list[i + 1][1] - new_ob_link_geometry_list[i][1]) ** 2) ** 0.5
                link.coord_length = new_ib_link_coord_length + new_ob_link_coord_length

                new_ib_link_breakpoint_list = [item * new_ib_link_coord_length / ib_link.coord_length for item in ib_link.breakpoint_list]
                new_ob_link_breakpoint_list = [item * new_ob_link_coord_length / ob_link.coord_length for item in ob_link.breakpoint_list]
                new_ob_link_breakpoint_list_con = [item + new_ib_link_coord_length for item in new_ob_link_breakpoint_list]

                if ib_link.number_of_lanes_list[-1] == ob_link.number_of_lanes_list[0]:
                    link.breakpoint_list = new_ib_link_breakpoint_list[:-1] + new_ob_link_breakpoint_list_con[1:]
                    link.number_of_lanes_list = ib_link.number_of_lanes_list + ob_link.number_of_lanes_list[1:]
                else:
                    link.breakpoint_list = new_ib_link_breakpoint_list + new_ob_link_breakpoint_list_con[1:]
                    link.number_of_lanes_list = ib_link.number_of_lanes_list + ob_link.number_of_lanes_list


                link.max_number_of_lanes = max(ib_link.max_number_of_lanes, ob_link.max_number_of_lanes)
                link.breakpoint_list = []
                link.number_of_lanes_list = []
                link.lanes_change_list = []



                self.number_of_combined_links += 1
                self.number_of_links += 1
