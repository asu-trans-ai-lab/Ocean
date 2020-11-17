# @author        Jiawei Lu
# @email         jiaweil9@asu.edu
# @create date   2020-04-16 16:32:41
# @desc          [description]


import numpy as np
from autoconintd import *
from autoconm import *
from queuearea import *
from exitprogram import *


class CNetGenerator:
    def __init__(self, macro_net, length_of_cell, length_of_cut, width_of_lane, auto_connection, cells_in_queue_area):
        self.macro_net = macro_net
        self.length_of_cell = length_of_cell
        self.length_of_cut = length_of_cut
        self.width_of_lane = width_of_lane
        self.auto_connection = auto_connection
        self.cells_in_queue_area = cells_in_queue_area

        self.number_of_micro_nodes = 0
        self.number_of_micro_links = 0
        self.number_of_meso_nodes = 0
        self.number_of_meso_links = 0

        self.micro_node_list = []
        self.micro_link_list = []
        self.meso_node_list = []
        self.meso_link_list = []

        self.meso_node_id_to_seq_no_dict = {}
        self.micro_node_id_to_seq_no_dict = {}
        self.meso_link_id_to_seq_no_dict = {}
        self.micro_link_id_to_seq_no_dict = {}

        self.meso_link_key_to_seq_no_dict = {}

        self.processed_node_id_set = set()

        self.qa = None

    
    def createMicroNetForNormalLink(self, link):

        first_micro_node = True

        for meso_link_id in link.meso_link_id_list:
            mesolink = self.meso_link_list[self.meso_link_id_to_seq_no_dict[meso_link_id]]
            original_number_of_lanes = mesolink.number_of_lanes_of_original_link
            lane_changes_left = mesolink.changes_of_lanes[0]
            num_of_lane_offset_between_left_most_and_central = -1 * (original_number_of_lanes / 2 - 0.5 + lane_changes_left)
            for section_no in range(len(mesolink.geometry_list)-1):
                lane_coord_list = []        # [lane1_from_coord, lane1_to_coord], [lane2_from_coord, lane2_to_coord]..
                from_coord = mesolink.geometry_list[section_no]
                to_coord = mesolink.geometry_list[section_no+1]
                delta_x = to_coord[0] - from_coord[0]
                delta_y = to_coord[1] - from_coord[1]
                length = (delta_x**2 + delta_y**2)**0.5
                mesolink.section_length_list.append(length)
                cell_offset_x = delta_x / length * self.length_of_cell
                cell_offset_y = delta_y / length * self.length_of_cell
                mesolink.section_cell_offset_list.append((cell_offset_x,cell_offset_y))

                for i in range(mesolink.number_of_lanes):
                    lane_offset = (num_of_lane_offset_between_left_most_and_central + i) * self.width_of_lane
                    offset_x = delta_y / length * lane_offset
                    offset_y = -1 * delta_x / length * lane_offset
                    lane_from_coord = (from_coord[0] + offset_x, from_coord[1] + offset_y)
                    lane_to_coord = (to_coord[0] + offset_x, to_coord[1] + offset_y)
                    lane_coord_list.append([lane_from_coord,lane_to_coord])

                mesolink.section_lane_coord_list.append(lane_coord_list)

            for section_no in range(len(mesolink.geometry_list)-1):
                remaining_length = mesolink.section_length_list[section_no]
                section_micro_node_id_list = [[] for _ in range(mesolink.number_of_lanes)]
            
                for i in range(mesolink.number_of_lanes):
                    micronode = micronet.CMicroNode()
                    micronode.node_id = self.number_of_micro_nodes
                    micronode.node_seq_no = self.number_of_micro_nodes
                    micronode.x_coord = mesolink.section_lane_coord_list[section_no][i][0][0]
                    micronode.y_coord = mesolink.section_lane_coord_list[section_no][i][0][1]
                    micronode.meso_link_id = mesolink.link_id
                    micronode.lane_no = i + 1

                    if first_micro_node:
                        micronode.activity_type = link.from_node.activity_type
                        micronode.is_boundary = link.from_node.is_boundary
                        first_micro_node = False

                    self.micro_node_list.append(micronode)
                    self.micro_node_id_to_seq_no_dict[micronode.node_id] = micronode.node_seq_no
                    section_micro_node_id_list[i].append(micronode.node_id)
                    self.number_of_micro_nodes += 1

                cell_no = 1
                while remaining_length > self.length_of_cell * 1.5:
                    for i in range(mesolink.number_of_lanes):
                        micronode = micronet.CMicroNode()
                        micronode.node_id = self.number_of_micro_nodes
                        micronode.node_seq_no = self.number_of_micro_nodes
                        micronode.x_coord = mesolink.section_lane_coord_list[section_no][i][0][0] + cell_no * mesolink.section_cell_offset_list[section_no][0]
                        micronode.y_coord = mesolink.section_lane_coord_list[section_no][i][0][1] + cell_no * mesolink.section_cell_offset_list[section_no][1]
                        micronode.meso_link_id = mesolink.link_id
                        micronode.lane_no = i + 1

                        self.micro_node_list.append(micronode)
                        self.micro_node_id_to_seq_no_dict[micronode.node_id] = micronode.node_seq_no
                        section_micro_node_id_list[i].append(micronode.node_id)
                        self.number_of_micro_nodes += 1
                    cell_no += 1
                    remaining_length -= self.length_of_cell
            
                for i in range(mesolink.number_of_lanes):
                    micronode = micronet.CMicroNode()
                    micronode.node_id = self.number_of_micro_nodes
                    micronode.node_seq_no = self.number_of_micro_nodes
                    micronode.x_coord = mesolink.section_lane_coord_list[section_no][i][1][0]
                    micronode.y_coord = mesolink.section_lane_coord_list[section_no][i][1][1]
                    micronode.meso_link_id = mesolink.link_id
                    micronode.lane_no = i + 1

                    self.micro_node_list.append(micronode)
                    self.micro_node_id_to_seq_no_dict[micronode.node_id] = micronode.node_seq_no
                    section_micro_node_id_list[i].append(micronode.node_id)
                    self.number_of_micro_nodes += 1

                mesolink.micro_node_id_list_for_each_section.append(section_micro_node_id_list)

            for i in range(len(mesolink.geometry_list)-2):
                upstream_section_no = i
                downstream_section_no = i + 1
                connection_node_id_list = []
                for j in range(mesolink.number_of_lanes):
                    uf = mesolink.section_lane_coord_list[upstream_section_no][j][0]
                    ut = mesolink.section_lane_coord_list[upstream_section_no][j][1]
                    df = mesolink.section_lane_coord_list[downstream_section_no][j][0]
                    dt = mesolink.section_lane_coord_list[downstream_section_no][j][1]
                    if ut == df:
                        x, y = ut
                    else:
                        A = [[ut[1]-uf[1],uf[0]-ut[0]],[dt[1]-df[1],df[0]-dt[0]]]
                        b = [(ut[1]-uf[1])*uf[0]-(ut[0]-uf[0])*uf[1],(dt[1]-df[1])*df[0]-(dt[0]-df[0])*df[1]]
                        A_mat = np.mat(A)
                        b_mat = np.mat(b).T
                        solution = np.linalg.inv(A_mat) * b_mat
                        x, y = solution[0,0], solution[1,0]

                    micronode = micronet.CMicroNode()
                    micronode.node_id = self.number_of_micro_nodes
                    micronode.node_seq_no = self.number_of_micro_nodes
                    micronode.x_coord = x
                    micronode.y_coord = y
                    micronode.meso_link_id = mesolink.link_id
                    micronode.lane_no = j + 1

                    self.micro_node_list.append(micronode)
                    self.micro_node_id_to_seq_no_dict[micronode.node_id] = micronode.node_seq_no
                    connection_node_id_list.append(micronode.node_id)
                    self.number_of_micro_nodes += 1
            
                mesolink.section_connection_node_id_list.append(connection_node_id_list)
        
            if len(mesolink.geometry_list) == 2:
                # one section
                for i in range(mesolink.number_of_lanes):
                    mesolink.micro_node_list.append(mesolink.micro_node_id_list_for_each_section[0][i])
            else:
                # more than one
                mesolink.micro_node_list = [[] for _ in range(mesolink.number_of_lanes)]
                for section_no in range(len(mesolink.geometry_list)-1):
                    section_micro_node_id_list = mesolink.micro_node_id_list_for_each_section[section_no]
                    if section_no == 0:
                        # keep the first micronode
                        for i in range(mesolink.number_of_lanes):
                            mesolink.micro_node_list[i] = section_micro_node_id_list[i][:-1]
                            mesolink.micro_node_list[i].append(mesolink.section_connection_node_id_list[section_no][i])
                            self.micro_node_list[self.micro_node_id_to_seq_no_dict[section_micro_node_id_list[i][-1]]].valid = False
                    elif section_no == len(mesolink.geometry_list)-2:
                        # keep the last micronode
                        for i in range(mesolink.number_of_lanes):
                            mesolink.micro_node_list[i] += section_micro_node_id_list[i][1:]
                            self.micro_node_list[self.micro_node_id_to_seq_no_dict[section_micro_node_id_list[i][0]]].valid = False
                    else:
                        # do not keep micronodes on two sides
                        for i in range(mesolink.number_of_lanes):
                            mesolink.micro_node_list[i] += section_micro_node_id_list[i][1:-1]
                            mesolink.micro_node_list[i].append(mesolink.section_connection_node_id_list[section_no][i])
                            self.micro_node_list[self.micro_node_id_to_seq_no_dict[section_micro_node_id_list[i][0]]].valid = False
                            self.micro_node_list[self.micro_node_id_to_seq_no_dict[section_micro_node_id_list[i][-1]]].valid = False


        for i in range(len(link.meso_link_id_list)-1):
            upstream_mesolink = self.meso_link_list[self.meso_link_id_to_seq_no_dict[link.meso_link_id_list[i]]]
            downstream_mesolink = self.meso_link_list[self.meso_link_id_to_seq_no_dict[link.meso_link_id_list[i+1]]]

            up_index_of_left_most_lane_of_original_link = upstream_mesolink.changes_of_lanes[0]
            down_index_of_left_most_lane_of_original_link = downstream_mesolink.changes_of_lanes[0]
            min_left_most_lane_index = min(up_index_of_left_most_lane_of_original_link, down_index_of_left_most_lane_of_original_link)
            up_lane_index_start = up_index_of_left_most_lane_of_original_link - min_left_most_lane_index
            down_lane_index_start = down_index_of_left_most_lane_of_original_link - min_left_most_lane_index

            number_of_connecting_lanes = min(upstream_mesolink.number_of_lanes-up_lane_index_start,
                                             downstream_mesolink.number_of_lanes-down_lane_index_start)

            for j in range(number_of_connecting_lanes):
                up_lane_index = up_lane_index_start + j
                down_lane_index = down_lane_index_start + j
                up_micro_node_id = upstream_mesolink.micro_node_list[up_lane_index][-1]
                down_micro_node_id = downstream_mesolink.micro_node_list[down_lane_index][0]

                upstream_mesolink.micro_node_list[up_lane_index][-1] = down_micro_node_id
                self.micro_node_list[self.micro_node_id_to_seq_no_dict[up_micro_node_id]].valid = False

        # create cell
        for meso_link_id in link.meso_link_id_list:
            mesolink = self.meso_link_list[self.meso_link_id_to_seq_no_dict[meso_link_id]]
            for i in range(mesolink.number_of_lanes):
                # travelling
                for j in range(len(mesolink.micro_node_list[i])-1):
                    from_node = self.micro_node_list[self.micro_node_id_to_seq_no_dict[mesolink.micro_node_list[i][j]]]
                    to_node = self.micro_node_list[self.micro_node_id_to_seq_no_dict[mesolink.micro_node_list[i][j+1]]]

                    microlink = micronet.CMicroLink()
                    microlink.link_id = self.number_of_micro_links
                    microlink.link_seq_no = self.number_of_micro_links
                    microlink.from_node_id = from_node.node_id
                    microlink.to_node_id = to_node.node_id
                    microlink.meso_link_id = mesolink.link_id
                    microlink.length = ((from_node.x_coord - to_node.x_coord)**2 + (from_node.y_coord - to_node.y_coord)**2)**0.5
                    microlink.speed_limit = mesolink.speed_limit
                    microlink.cell_type = 1	            # //1:traveling; 2:changing
                    microlink.additional_cost = 0.0
                    self.number_of_micro_links += 1
                    self.micro_link_list.append(microlink)
                    self.micro_link_id_to_seq_no_dict[microlink.link_id] = microlink.link_seq_no
                    from_node.m_outgoing_link_list.append(microlink.link_id)
                    to_node.m_incoming_link_list.append(microlink.link_id)

                # changing
                if i <= mesolink.number_of_lanes - 2:
                    # to left
                    for j in range(len(mesolink.micro_node_list[i])-1):
                        from_node = self.micro_node_list[self.micro_node_id_to_seq_no_dict[mesolink.micro_node_list[i][j]]]
                        to_node = self.micro_node_list[self.micro_node_id_to_seq_no_dict[mesolink.micro_node_list[i+1][j+1]]]
                        microlink = micronet.CMicroLink()
                        microlink.link_id = self.number_of_micro_links
                        microlink.link_seq_no = self.number_of_micro_links
                        microlink.from_node_id = from_node.node_id
                        microlink.to_node_id = to_node.node_id
                        microlink.meso_link_id = mesolink.link_id
                        microlink.length = ((from_node.x_coord - to_node.x_coord)**2 + (from_node.y_coord - to_node.y_coord)**2)**0.5
                        microlink.speed_limit = mesolink.speed_limit
                        microlink.cell_type = 2	            # //1:traveling; 2:changing
                        microlink.additional_cost = 2.0
                        self.number_of_micro_links += 1
                        self.micro_link_list.append(microlink)
                        self.micro_link_id_to_seq_no_dict[microlink.link_id] = microlink.link_seq_no
                        from_node.m_outgoing_link_list.append(microlink.link_id)
                        to_node.m_incoming_link_list.append(microlink.link_id)
            
                if i >= 1:
                    # to right
                    for j in range(len(mesolink.micro_node_list[i])-1):
                        from_node = self.micro_node_list[self.micro_node_id_to_seq_no_dict[mesolink.micro_node_list[i][j]]]
                        to_node = self.micro_node_list[self.micro_node_id_to_seq_no_dict[mesolink.micro_node_list[i-1][j+1]]]
                        microlink = micronet.CMicroLink()
                        microlink.link_id = self.number_of_micro_links
                        microlink.link_seq_no = self.number_of_micro_links
                        microlink.from_node_id = from_node.node_id
                        microlink.to_node_id = to_node.node_id
                        microlink.meso_link_id = mesolink.link_id
                        microlink.length = ((from_node.x_coord - to_node.x_coord)**2 + (from_node.y_coord - to_node.y_coord)**2)**0.5
                        microlink.speed_limit = mesolink.speed_limit
                        microlink.cell_type = 2	            # //1:traveling; 2:changing
                        microlink.additional_cost = 2.0
                        self.number_of_micro_links += 1
                        self.micro_link_list.append(microlink)
                        self.micro_link_id_to_seq_no_dict[microlink.link_id] = microlink.link_seq_no
                        from_node.m_outgoing_link_list.append(microlink.link_id)
                        to_node.m_incoming_link_list.append(microlink.link_id)


    def createMicroNetForConnector(self, mesolink,ib_mesolink,ib_lane_index_start,ob_mesolink,ob_lane_index_start):

        for i in range(mesolink.number_of_lanes):
            start_micronode = self.micro_node_list[self.micro_node_id_to_seq_no_dict[ib_mesolink.micro_node_list[ib_lane_index_start+i][-1]]]
            end_micronode = self.micro_node_list[self.micro_node_id_to_seq_no_dict[ob_mesolink.micro_node_list[ob_lane_index_start+i][0]]]
            total_length = ((start_micronode.x_coord - end_micronode.x_coord)**2 + (start_micronode.y_coord - end_micronode.y_coord)**2)**0.5
            cell_offset_x = (end_micronode.x_coord - start_micronode.x_coord) / total_length * self.length_of_cell
            cell_offset_y = (end_micronode.y_coord - start_micronode.y_coord) / total_length * self.length_of_cell

            mesolink.micro_node_list.append([])
            mesolink.micro_link_list.append([])

            last_micronode = start_micronode
            remaining_length = total_length

            first_cell = True

            while remaining_length > self.length_of_cell * 1.5:
                micronode = micronet.CMicroNode()
                micronode.node_id = self.number_of_micro_nodes
                micronode.node_seq_no = self.number_of_micro_nodes
                micronode.x_coord = last_micronode.x_coord + cell_offset_x
                micronode.y_coord = last_micronode.y_coord + cell_offset_y
                micronode.meso_link_id = mesolink.link_id
                micronode.lane_no = i + 1

                self.micro_node_list.append(micronode)
                self.micro_node_id_to_seq_no_dict[micronode.node_id] = micronode.node_seq_no
                mesolink.micro_node_list[-1].append(micronode)
                self.number_of_micro_nodes += 1

                microlink = micronet.CMicroLink()
                microlink.link_id = self.number_of_micro_links
                microlink.link_seq_no = self.number_of_micro_links
                microlink.from_node_id = last_micronode.node_id
                microlink.to_node_id = micronode.node_id
                microlink.meso_link_id = mesolink.link_id
                microlink.length = self.length_of_cell
                microlink.speed_limit = mesolink.speed_limit
                microlink.cell_type = 1	            # //1:traveling; 2:changing
                microlink.additional_cost = 0.0
                if first_cell: microlink.movement_str = mesolink.movement_str
                self.number_of_micro_links += 1
                self.micro_link_list.append(microlink)
                self.micro_link_id_to_seq_no_dict[microlink.link_id] = microlink.link_seq_no
                mesolink.micro_link_list[-1].append(microlink)
                last_micronode.m_outgoing_link_list.append(microlink.link_id)
                micronode.m_incoming_link_list.append(microlink.link_id)

                remaining_length -= self.length_of_cell
                last_micronode = micronode
                first_cell = False

            microlink = micronet.CMicroLink()
            microlink.link_id = self.number_of_micro_links
            microlink.link_seq_no = self.number_of_micro_links
            microlink.from_node_id = last_micronode.node_id
            microlink.to_node_id = end_micronode.node_id
            microlink.meso_link_id = mesolink.link_id
            microlink.length = ((last_micronode.x_coord - end_micronode.x_coord)**2 + (last_micronode.y_coord - end_micronode.y_coord)**2)**0.5
            microlink.speed_limit = mesolink.speed_limit
            microlink.cell_type = 1	            # //1:traveling; 2:changing
            microlink.additional_cost = 0.0
            if first_cell: microlink.movement_str = mesolink.movement_str
            self.number_of_micro_links += 1
            self.micro_link_list.append(microlink)
            self.micro_link_id_to_seq_no_dict[microlink.link_id] = microlink.link_seq_no
            mesolink.micro_link_list[-1].append(microlink)
            last_micronode.m_outgoing_link_list.append(microlink.link_id)
            end_micronode.m_incoming_link_list.append(microlink.link_id)


    def initializeLinks(self):
        print('Initilizing original links...')
        for link in self.macro_net.link_list:
            if not link.valid: continue

            downstream_max_cut = max(link.length_of_short_cut, link.breakpoint_list[-1] - link.breakpoint_list[-2] - 3)

            if link.upstream_short_cut and link.downstream_short_cut:
                if link.coord_length <= 2 * link.length_of_short_cut:
                    print(f'Unable to initialize link {link.link_id}')
                    exitProgram()
                link.length_of_cut_upstream = link.length_of_short_cut
                link.length_of_cut_downstream = link.length_of_short_cut
            elif link.upstream_short_cut or link.downstream_short_cut:
                length_found = False
                ii = 0
                for i in range(link.number_of_lanes_list[-1], -1, -1):
                    if link.coord_length > self.length_of_cut[i] + link.length_of_short_cut:
                        ii = i
                        length_found = True
                        break
                if not length_found:
                    print(f'Unable to initialize link {link.link_id}')
                    exitProgram()
                if link.upstream_short_cut:
                    link.length_of_cut_upstream = link.length_of_short_cut
                    link.length_of_cut_downstream = min(downstream_max_cut, self.length_of_cut[ii])
                else:
                    link.length_of_cut_upstream = self.length_of_cut[ii]
                    link.length_of_cut_downstream = link.length_of_short_cut
            else:

                length_found = False
                ii = 0
                for i in range(link.number_of_lanes_list[-1], -1, -1):
                    if link.coord_length > 2 * self.length_of_cut[i]:
                        ii = i
                        length_found = True
                        break
                if not length_found:
                    print(f'Unable to initialize link {link.link_id}')
                    exitProgram()

                link.length_of_cut_upstream = self.length_of_cut[ii]
                link.length_of_cut_downstream = min(downstream_max_cut, self.length_of_cut[ii])

            link.Initialization()


    def createMesoNodeForCentriod(self):
        # create new meso nodes for centroids
        for node in self.macro_net.node_list:
            if node.is_centroid and node.valid:
                meso_node = mesonet.CMesoNode()
                meso_node.node_id = node.node_id * 100 + node.number_of_expanded_mesonode
                meso_node.node_seq_no = self.number_of_meso_nodes
                meso_node.x_coord = node.x_coord
                meso_node.y_coord = node.y_coord
                meso_node.original_node_id = node.node_id
                meso_node.zone_id = node.zone_id
                self.meso_node_list.append(meso_node)
                self.number_of_meso_nodes += 1
                node.number_of_expanded_mesonode += 1
                self.meso_node_id_to_seq_no_dict[meso_node.node_id] = meso_node.node_seq_no
                node.centroid_meso_node = meso_node


    def createNormalLinks(self):
        # normal mesolink
        print('Generating normal meso links...')
        for link in self.macro_net.link_list:
            if not link.valid: continue

            if link.from_node.is_centroid:
                upstream_node = link.from_node.centroid_meso_node
            else:
                upstream_node = mesonet.CMesoNode()
                upstream_node.node_id = link.from_node.node_id * 100 + link.from_node.number_of_expanded_mesonode
                upstream_node.node_seq_no = self.number_of_meso_nodes
                upstream_node.x_coord = link.cutted_geometry_list[0][0][0]
                upstream_node.y_coord = link.cutted_geometry_list[0][0][1]
                upstream_node.original_node_id = link.from_node_id
                upstream_node.zone_id = link.from_node.zone_id
                upstream_node.activity_type = link.from_node.activity_type
                upstream_node.is_boundary = link.from_node.is_boundary
                self.meso_node_list.append(upstream_node)
                self.number_of_meso_nodes += 1
                link.from_node.number_of_expanded_mesonode += 1
                self.meso_node_id_to_seq_no_dict[upstream_node.node_id] = upstream_node.node_seq_no

            for section_no in range(link.cutted_number_of_sections):

                if link.to_node.is_centroid and section_no == link.cutted_number_of_sections - 1:
                    downstream_node = link.to_node.centroid_meso_node
                else:
                    downstream_node = mesonet.CMesoNode()
                    downstream_node.node_id = link.to_node.node_id * 100 + link.to_node.number_of_expanded_mesonode
                    downstream_node.node_seq_no = self.number_of_meso_nodes
                    downstream_node.x_coord = link.cutted_geometry_list[section_no][-1][0]
                    downstream_node.y_coord = link.cutted_geometry_list[section_no][-1][1]
                    if section_no == link.cutted_number_of_sections - 1:
                        downstream_node.original_node_id = link.to_node_id
                        downstream_node.zone_id = link.to_node.zone_id
                        downstream_node.activity_type = link.to_node.activity_type
                        downstream_node.is_boundary = link.to_node.is_boundary
                    self.meso_node_list.append(downstream_node)
                    self.number_of_meso_nodes += 1
                    link.to_node.number_of_expanded_mesonode += 1
                    self.meso_node_id_to_seq_no_dict[downstream_node.node_id] = downstream_node.node_seq_no

                mesolink = mesonet.CMesoLink()
                mesolink.link_id = self.number_of_meso_links
                mesolink.link_seq_no = self.number_of_meso_links
                mesolink.from_node_id = upstream_node.node_id
                mesolink.to_node_id = downstream_node.node_id
                mesolink.link_type = link.link_type
                mesolink.TMC = link.TMC
                mesolink.number_of_lanes = link.cutted_number_of_lanes_list[section_no]
                mesolink.number_of_lanes_of_original_link = link.number_of_lanes
                mesolink.changes_of_lanes = link.cutted_lanes_change_list[section_no]
                mesolink.speed_limit = link.speed_limit
                mesolink.lane_cap = link.lane_cap
                mesolink.geometry_list = link.cutted_geometry_list[section_no]
                for i in range(len(mesolink.geometry_list)-1):
                    mesolink.length += ((mesolink.geometry_list[i+1][0] - mesolink.geometry_list[i][0])**2 + (mesolink.geometry_list[i+1][1] - mesolink.geometry_list[i][1])**2)**0.5
                mesolink.original_link_id = link.link_id

                self.meso_link_list.append(mesolink)
                self.number_of_meso_links += 1
                self.meso_link_id_to_seq_no_dict[mesolink.link_id] = mesolink.link_seq_no
                link.meso_link_id_list.append(mesolink.link_id)

                upstream_node.m_outgoing_link_list.append(mesolink.link_id)
                downstream_node.m_incoming_link_list.append(mesolink.link_id)

                upstream_node = downstream_node

            self.createMicroNetForNormalLink(link)


    def connectMesoLinksMVMT(self):
        # connector
        print('Generating connector links...')
        for mvmt in self.macro_net.movement_list:
            # print('mvmt',mvmt.movement_id)
            # if mvmt.movement_id == 6334:
            #     a = 1
            # node = self.macro_net.node_list[self.macro_net.node_id_to_seq_no_dict[mvmt.node_id]]
            # if not node.valid: continue

            ib_link = self.macro_net.link_list[self.macro_net.link_id_to_seq_no_dict[mvmt.ib_link_id]]
            if not ib_link.valid: continue
            ib_lane = mvmt.ib_lane
            ob_link = self.macro_net.link_list[self.macro_net.link_id_to_seq_no_dict[mvmt.ob_link_id]]
            if not ob_link.valid: continue
            ob_lane = mvmt.ob_lane

            self.processed_node_id_set.add(ib_link.to_node_id)

            if (ib_lane == 'nan') or (ob_lane == 'nan'):
                print('  warning: no ib_lane or ob_lane info is provided at movement {}, movement info will be discarded.'.format(mvmt.movement_id))
                continue

            ib_mesolink = self.meso_link_list[self.meso_link_id_to_seq_no_dict[ib_link.meso_link_id_list[-1]]]
            ib_lane_list = list(map(int,ib_lane.split('|')))
            ob_mesolink = self.meso_link_list[self.meso_link_id_to_seq_no_dict[ob_link.meso_link_id_list[0]]]
            ob_lane_list = list(map(int,ob_lane.split('|')))

            if len(ib_lane_list) != len(ob_lane_list):
                print('  warning: number of inbound lanes and outbound lanes at movement {} is not consistent, movement info will be discarded'.format(mvmt.movement_id))
                continue
            if (0 in ib_lane_list) or (0 in ob_lane_list):
                print('  warning: lane number 0 detected at movement {}, movement info will be discarded'.format(mvmt.movement_id))
                continue
            number_of_lanes = len(ib_lane_list)

            # lane index starts from 0
            ib_lane_index_start = ib_mesolink.changes_of_lanes[0] + ib_lane_list[0] if ib_lane_list[0] < 0 else ib_mesolink.changes_of_lanes[0] + ib_lane_list[0] - 1
            ib_lane_index_end = ib_mesolink.changes_of_lanes[0] + ib_lane_list[-1] if ib_lane_list[-1] < 0 else ib_mesolink.changes_of_lanes[0] + ib_lane_list[-1] - 1
            ob_lane_index_start = ob_mesolink.changes_of_lanes[0] + ob_lane_list[0] if ob_lane_list[0] < 0 else ob_mesolink.changes_of_lanes[0] + ob_lane_list[0] - 1
            ob_lane_index_end = ob_mesolink.changes_of_lanes[0] + ob_lane_list[-1] if ob_lane_list[-1] < 0 else ob_mesolink.changes_of_lanes[0] + ob_lane_list[-1] - 1

            if (ib_lane_index_start < 0) or (ob_lane_index_start < 0) or (ib_lane_index_end > ib_mesolink.number_of_lanes - 1) or (ob_lane_index_end > ob_mesolink.number_of_lanes - 1):
                print('  warning: inbound or outbound lane info of movement {} is not consistent with what inbound or outbound link has,'
                      ' movement info will be discarded'.format(mvmt.movement_id))
                continue

            # check if movement link is needed
            macro_node = ib_link.to_node
            if macro_node.movement_link_needed:
                # need movement link
                mesolink = mesonet.CMesoLink()
                mesolink.link_id = self.number_of_meso_links
                mesolink.link_seq_no = self.number_of_meso_links
                mesolink.from_node_id = ib_mesolink.to_node_id
                mesolink.to_node_id = ob_mesolink.from_node_id
                mesolink.link_type = 20
                mesolink.number_of_lanes = number_of_lanes
                mesolink.speed_limit = ib_mesolink.speed_limit
                mesolink.lane_cap = ib_mesolink.lane_cap
                mesolink.isconnector = True
                mesolink.movement_str = mvmt.movement_str
                mesolink.main_node_id = ib_link.to_node.main_node_id

                if ib_link.to_node.control_type == 1:
                    ib_start, ib_end = ib_mesolink.geometry_list[0], ib_mesolink.geometry_list[-1]
                    ob_start, ob_end = ob_mesolink.geometry_list[0], ob_mesolink.geometry_list[-1]
                    mesolink.movement_str = getMovementStr(ib_start, ib_end, ob_start, ob_end)

                try:
                    up_start_lane_coord = ib_mesolink.section_lane_coord_list[-1][ib_lane_index_start][1]
                    up_end_lane_coord = ib_mesolink.section_lane_coord_list[-1][ib_lane_index_end][1]
                    from_x_coord = (up_start_lane_coord[0] + up_end_lane_coord[0]) / 2
                    from_y_coord = (up_start_lane_coord[1] + up_end_lane_coord[1]) / 2
                    down_start_lane_coord = ob_mesolink.section_lane_coord_list[0][ob_lane_index_start][0]
                    down_end_lane_coord = ob_mesolink.section_lane_coord_list[0][ob_lane_index_end][0]
                    to_x_coord = (down_start_lane_coord[0] + down_end_lane_coord[0]) / 2
                    to_y_coord = (down_start_lane_coord[1] + down_end_lane_coord[1]) / 2
                except IndexError:
                    print('  other error'.format(mvmt.movement_id))
                    continue

                mesolink.geometry_list = [(from_x_coord, from_y_coord), (to_x_coord, to_y_coord)]
                mesolink.geometry_list_no_lane_offset = [ib_mesolink.geometry_list[-1], ob_mesolink.geometry_list[0]]

                for i in range(len(mesolink.geometry_list) - 1):
                    mesolink.length += ((mesolink.geometry_list[i + 1][0] - mesolink.geometry_list[i][0]) ** 2 + (mesolink.geometry_list[i + 1][1] - mesolink.geometry_list[i][1]) ** 2) ** 0.5

                self.meso_link_list.append(mesolink)
                self.number_of_meso_links += 1
                self.meso_link_id_to_seq_no_dict[mesolink.link_id] = mesolink.link_seq_no

                from_node = self.meso_node_list[self.meso_node_id_to_seq_no_dict[mesolink.from_node_id]]
                from_node.m_outgoing_link_list.append(mesolink.link_id)
                to_node = self.meso_node_list[self.meso_node_id_to_seq_no_dict[mesolink.to_node_id]]
                to_node.m_incoming_link_list.append(mesolink.link_id)

                self.createMicroNetForConnector(mesolink, ib_mesolink, ib_lane_index_start, ob_mesolink, ob_lane_index_start)
            else:
                # no movemnt link
                if ib_link.downstream_is_target and not ob_link.upstream_is_target:
                    # remove incoming micro nodes and links of ob_mesolink, then connect to ib_mesolink
                    ib_mesolink_to_node = self.meso_node_list[self.meso_node_id_to_seq_no_dict[ib_mesolink.to_node_id]]
                    ob_mesolink_from_node = self.meso_node_list[self.meso_node_id_to_seq_no_dict[ob_mesolink.from_node_id]]
                    ob_mesolink_from_node.valid = False
                    ob_mesolink.from_node_id = ib_mesolink_to_node.node_id
                    ob_mesolink.geometry_list[0] = ib_mesolink.geometry_list[-1]

                    for i in range(number_of_lanes):
                        ib_lane_index = ib_lane_index_start + i
                        ob_lane_index = ob_lane_index_start + i
                        ib_mesolink_outgoing_micro_node_id = ib_mesolink.micro_node_list[ib_lane_index][-1]
                        ib_mesolink_outgoing_micro_node = self.micro_node_list[self.micro_node_id_to_seq_no_dict[ib_mesolink_outgoing_micro_node_id]]
                        ob_mesolink_incoming_micro_node_id = ob_mesolink.micro_node_list[ob_lane_index][0]
                        ob_mesolink_incoming_micro_node = self.micro_node_list[self.micro_node_id_to_seq_no_dict[ob_mesolink_incoming_micro_node_id]]
                        ob_mesolink_incoming_micro_node.valid = False
                        for microlink_id in ob_mesolink_incoming_micro_node.m_outgoing_link_list:
                            microlink = self.micro_link_list[self.micro_link_id_to_seq_no_dict[microlink_id]]
                            microlink.from_node_id = ib_mesolink_outgoing_micro_node.node_id
                elif not ib_link.downstream_is_target and ob_link.upstream_is_target:
                    # remove outgoing micro nodes and links of ib_mesolink, then connect to ob_mesolink
                    ib_mesolink_to_node = self.meso_node_list[self.meso_node_id_to_seq_no_dict[ib_mesolink.to_node_id]]
                    ob_mesolink_from_node = self.meso_node_list[self.meso_node_id_to_seq_no_dict[ob_mesolink.from_node_id]]
                    ib_mesolink_to_node.valid = False
                    ib_mesolink.to_node_id = ob_mesolink_from_node.node_id
                    ib_mesolink.geometry_list[-1] = ob_mesolink.geometry_list[0]

                    for i in range(number_of_lanes):
                        ib_lane_index = ib_lane_index_start + i
                        ob_lane_index = ob_lane_index_start + i
                        ib_mesolink_outgoing_micro_node_id = ib_mesolink.micro_node_list[ib_lane_index][-1]
                        ib_mesolink_outgoing_micro_node = self.micro_node_list[self.micro_node_id_to_seq_no_dict[ib_mesolink_outgoing_micro_node_id]]
                        ob_mesolink_incoming_micro_node_id = ob_mesolink.micro_node_list[ob_lane_index][0]
                        ob_mesolink_incoming_micro_node = self.micro_node_list[self.micro_node_id_to_seq_no_dict[ob_mesolink_incoming_micro_node_id]]
                        ib_mesolink_outgoing_micro_node.valid = False
                        for microlink_id in ib_mesolink_outgoing_micro_node.m_incoming_link_list:
                            microlink = self.micro_link_list[self.micro_link_id_to_seq_no_dict[microlink_id]]
                            microlink.to_node_id = ob_mesolink_incoming_micro_node.node_id
                else:
                    # only one target link is allowed
                    print('Target link defintion error')
                    exitProgram()


    def connectMesoLinkAUTO(self):
        # use autocon to connect links without movement information
        if not self.auto_connection: return

        # connect links do not need movement links
        for node in self.macro_net.node_list:
            if not node.valid: continue
            if node.node_id in self.processed_node_id_set: continue
            if node.movement_link_needed: continue
            if len(node.m_incoming_link_list) == 1:
                # one ib link, diverge
                ib_link = self.macro_net.link_list[self.macro_net.link_id_to_seq_no_dict[node.m_incoming_link_list[0]]]
                ib_mesolink = self.meso_link_list[self.meso_link_id_to_seq_no_dict[ib_link.meso_link_id_list[-1]]]
                ob_mesolink_list = []
                for ob_link_id in node.m_outgoing_link_list:
                    ob_link = self.macro_net.link_list[self.macro_net.link_id_to_seq_no_dict[ob_link_id]]
                    if ib_link.from_node_id == ob_link.to_node_id: continue
                    ob_mesolink = self.meso_link_list[self.meso_link_id_to_seq_no_dict[ob_link.meso_link_id_list[0]]]
                    ob_mesolink_list.append(ob_mesolink)
                if len(ob_mesolink_list) == 0: continue
                CAutoConnectorIntD.ib_link, CAutoConnectorIntD.ob_link_list = ib_mesolink, ob_mesolink_list
                connection_list = CAutoConnectorIntD.buildConnector()

                for ob_mesolink_no, ob_mesolink in enumerate(ob_mesolink_list):
                    ib_mesolink_to_node = self.meso_node_list[self.meso_node_id_to_seq_no_dict[ib_mesolink.to_node_id]]
                    ob_mesolink_from_node = self.meso_node_list[self.meso_node_id_to_seq_no_dict[ob_mesolink.from_node_id]]
                    ob_mesolink_from_node.valid = False
                    ob_mesolink.from_node_id = ib_mesolink_to_node.node_id
                    ob_mesolink.geometry_list[0] = ib_mesolink.geometry_list[-1]
                    ib_lane_index_start = connection_list[ob_mesolink_no][0][0]
                    ib_lane_index_end = connection_list[ob_mesolink_no][0][1]
                    ob_lane_index_start = connection_list[ob_mesolink_no][1][0]
                    # ob_lane_index_end = connection_list[ob_mesolink_no][1][1]
                    number_of_lanes = ib_lane_index_end - ib_lane_index_start + 1
                    for i in range(number_of_lanes):
                        ib_lane_index = ib_lane_index_start + i
                        ob_lane_index = ob_lane_index_start + i
                        ib_mesolink_outgoing_micro_node_id = ib_mesolink.micro_node_list[ib_lane_index][-1]
                        ib_mesolink_outgoing_micro_node = self.micro_node_list[self.micro_node_id_to_seq_no_dict[ib_mesolink_outgoing_micro_node_id]]
                        ob_mesolink_incoming_micro_node_id = ob_mesolink.micro_node_list[ob_lane_index][0]
                        ob_mesolink_incoming_micro_node = self.micro_node_list[self.micro_node_id_to_seq_no_dict[ob_mesolink_incoming_micro_node_id]]
                        ob_mesolink_incoming_micro_node.valid = False
                        for microlink_id in ob_mesolink_incoming_micro_node.m_outgoing_link_list:
                            microlink = self.micro_link_list[self.micro_link_id_to_seq_no_dict[microlink_id]]
                            microlink.from_node_id = ib_mesolink_outgoing_micro_node.node_id
            else:
                # one ob link, merge
                ob_link = self.macro_net.link_list[self.macro_net.link_id_to_seq_no_dict[node.m_outgoing_link_list[0]]]
                ob_mesolink = self.meso_link_list[self.meso_link_id_to_seq_no_dict[ob_link.meso_link_id_list[0]]]
                ib_mesolink_list = []
                for ib_link_id in node.m_incoming_link_list:
                    ib_link = self.macro_net.link_list[self.macro_net.link_id_to_seq_no_dict[ib_link_id]]
                    if ib_link.from_node_id == ob_link.to_node_id: continue
                    ib_mesolink = self.meso_link_list[self.meso_link_id_to_seq_no_dict[ib_link.meso_link_id_list[-1]]]
                    ib_mesolink_list.append(ib_mesolink)
                if len(ib_mesolink_list) == 0: continue
                CAutoConnectorM.ob_link, CAutoConnectorM.ib_link_list = ob_mesolink, ib_mesolink_list
                connection_list = CAutoConnectorM.buildConnector()

                for ib_mesolink_no, ib_mesolink in enumerate(ib_mesolink_list):
                    ib_mesolink_to_node = self.meso_node_list[self.meso_node_id_to_seq_no_dict[ib_mesolink.to_node_id]]
                    ob_mesolink_from_node = self.meso_node_list[self.meso_node_id_to_seq_no_dict[ob_mesolink.from_node_id]]
                    ib_mesolink_to_node.valid = False
                    ib_mesolink.to_node_id = ob_mesolink_from_node.node_id
                    ib_mesolink.geometry_list[-1] = ob_mesolink.geometry_list[0]
                    ib_lane_index_start = connection_list[ib_mesolink_no][0][0]
                    ib_lane_index_end = connection_list[ib_mesolink_no][0][1]
                    ob_lane_index_start = connection_list[ib_mesolink_no][1][0]
                    # ob_lane_index_end = connection_list[ob_mesolink_no][1][1]
                    number_of_lanes = ib_lane_index_end - ib_lane_index_start + 1
                    for i in range(number_of_lanes):
                        ib_lane_index = ib_lane_index_start + i
                        ob_lane_index = ob_lane_index_start + i
                        ib_mesolink_outgoing_micro_node_id = ib_mesolink.micro_node_list[ib_lane_index][-1]
                        ib_mesolink_outgoing_micro_node = self.micro_node_list[self.micro_node_id_to_seq_no_dict[ib_mesolink_outgoing_micro_node_id]]
                        ob_mesolink_incoming_micro_node_id = ob_mesolink.micro_node_list[ob_lane_index][0]
                        ob_mesolink_incoming_micro_node = self.micro_node_list[self.micro_node_id_to_seq_no_dict[ob_mesolink_incoming_micro_node_id]]
                        ib_mesolink_outgoing_micro_node.valid = False
                        for microlink_id in ib_mesolink_outgoing_micro_node.m_incoming_link_list:
                            microlink = self.micro_link_list[self.micro_link_id_to_seq_no_dict[microlink_id]]
                            microlink.to_node_id = ob_mesolink_incoming_micro_node.node_id
            self.processed_node_id_set.add(node.node_id)


        # connect links need movement links
        for ib_link in self.macro_net.link_list:
            if not ib_link.valid: continue
            if ib_link.to_node.is_centroid: continue
            if ib_link.to_node_id in self.processed_node_id_set: continue
            else:
                ib_mesolink = self.meso_link_list[self.meso_link_id_to_seq_no_dict[ib_link.meso_link_id_list[-1]]]
                ob_mesolink_list = []
                node = self.macro_net.node_list[self.macro_net.node_id_to_seq_no_dict[ib_link.to_node_id]]
                for link_id in node.m_outgoing_link_list:
                    ob_link = self.macro_net.link_list[self.macro_net.link_id_to_seq_no_dict[link_id]]
                    if ib_link.from_node_id == ob_link.to_node_id: continue
                    ob_mesolink = self.meso_link_list[self.meso_link_id_to_seq_no_dict[ob_link.meso_link_id_list[0]]]
                    ob_mesolink_list.append(ob_mesolink)
                if len(ob_mesolink_list) == 0: continue

                CAutoConnectorIntD.ib_link, CAutoConnectorIntD.ob_link_list = ib_mesolink, ob_mesolink_list
                connection_list = CAutoConnectorIntD.buildConnector()

                for ob_mesolink_no, ob_mesolink in enumerate(ob_mesolink_list):

                    ib_lane_index_start = connection_list[ob_mesolink_no][0][0]
                    ib_lane_index_end = connection_list[ob_mesolink_no][0][1]
                    ob_lane_index_start = connection_list[ob_mesolink_no][1][0]
                    ob_lane_index_end = connection_list[ob_mesolink_no][1][1]

                    mesolink = mesonet.CMesoLink()
                    mesolink.link_id = self.number_of_meso_links
                    mesolink.link_seq_no = self.number_of_meso_links
                    mesolink.from_node_id = ib_mesolink.to_node_id
                    mesolink.to_node_id = ob_mesolink.from_node_id
                    mesolink.link_type = 20
                    mesolink.number_of_lanes = ib_lane_index_end - ib_lane_index_start + 1
                    mesolink.speed_limit = ib_mesolink.speed_limit
                    mesolink.lane_cap = ib_mesolink.lane_cap
                    mesolink.isconnector = True

                    up_start_lane_coord = ib_mesolink.section_lane_coord_list[-1][ib_lane_index_start][1]
                    up_end_lane_coord = ib_mesolink.section_lane_coord_list[-1][ib_lane_index_end][1]
                    from_x_coord = (up_start_lane_coord[0] + up_end_lane_coord[0]) / 2
                    from_y_coord = (up_start_lane_coord[1] + up_end_lane_coord[1]) / 2
                    down_start_lane_coord = ob_mesolink.section_lane_coord_list[0][ob_lane_index_start][0]
                    down_end_lane_coord = ob_mesolink.section_lane_coord_list[0][ob_lane_index_end][0]
                    to_x_coord = (down_start_lane_coord[0] + down_end_lane_coord[0]) / 2
                    to_y_coord = (down_start_lane_coord[1] + down_end_lane_coord[1]) / 2

                    mesolink.geometry_list = [(from_x_coord, from_y_coord), (to_x_coord, to_y_coord)]
                    mesolink.geometry_list_no_lane_offset = [ib_mesolink.geometry_list[-1], ob_mesolink.geometry_list[0]]

                    mesolink.main_node_id = ib_link.to_node.main_node_id
                    # ==========================================

                    if ib_link.to_node.control_type == 1:       # if ib_link.to_node.control_type == 1:
                        ib_start, ib_end = ib_mesolink.geometry_list[0], ib_mesolink.geometry_list[-1]
                        ob_start, ob_end = ob_mesolink.geometry_list[0], ob_mesolink.geometry_list[-1]
                        mesolink.movement_str = getMovementStr(ib_start, ib_end, ob_start, ob_end)

                    for i in range(len(mesolink.geometry_list) - 1):
                        mesolink.length += ((mesolink.geometry_list[i + 1][0] - mesolink.geometry_list[i][0]) ** 2 + (
                                    mesolink.geometry_list[i + 1][1] - mesolink.geometry_list[i][1]) ** 2) ** 0.5

                    self.meso_link_list.append(mesolink)
                    self.number_of_meso_links += 1
                    self.meso_link_id_to_seq_no_dict[mesolink.link_id] = mesolink.link_seq_no

                    self.createMicroNetForConnector(mesolink, ib_mesolink, ib_lane_index_start, ob_mesolink,
                                                    ob_lane_index_start)


    def generateNet(self):
        self.initializeLinks()
        self.createMesoNodeForCentriod()
        self.createNormalLinks()
        self.connectMesoLinksMVMT()
        self.connectMesoLinkAUTO()

        if self.cells_in_queue_area > 0:
            qa = CQueueArea(self)
            self.qa = qa
            qa.initialize()
            qa.createQueueArea()


def getMovementStr(ib_start, ib_end, ob_start, ob_end):
    angle_ib = math.atan2(ib_end[1] - ib_start[1], ib_end[0] - ib_start[0])
    if -0.75 * math.pi <= angle_ib < -0.25 * math.pi:
        direction = 'SB'
    elif -0.25 * math.pi <= angle_ib < 0.25 * math.pi:
        direction = 'EB'
    elif 0.25 * math.pi <= angle_ib < 0.75 * math.pi:
        direction = 'NB'
    else:
        direction = 'WB'

    angle_ob = math.atan2(ob_end[1] - ob_start[1], ob_end[0] - ob_start[0])
    angle = angle_ob - angle_ib
    if angle < -1 * math.pi:
        angle += 2 * math.pi
    if angle > math.pi:
        angle -= 2 * math.pi

    if angle > 0.25 * math.pi:
        mvmt = 'L'
    elif angle < -0.25 * math.pi:
        mvmt = 'R'
    else:
        mvmt = 'T'

    mvmt_str = direction + mvmt
    return mvmt_str
