# @author        Jiawei Lu
# @email         jiaweil9@asu.edu
# @create date   2020-04-16 17:08:03
# @desc          [description]

import os
import csv

def coordinateBack(macro_net, net_generator,connector_geometry_for_output):
    if macro_net.coordinate_type == 'm':
        for node in macro_net.node_list:
            if not node.valid: continue
            node.x_coord_original_type, node.y_coord_original_type = node.x_coord, node.y_coord
        for link in macro_net.link_list:
            if not link.valid: continue
            link.geometry_list_original_type = link.geometry_list
        for mesonode in net_generator.meso_node_list:
            if not mesonode.valid: continue
            mesonode.x_coord_original_type, mesonode.y_coord_original_type = mesonode.x_coord, mesonode.y_coord
        for mesolink in net_generator.meso_link_list:
            if not mesolink.valid: continue
            if connector_geometry_for_output == 2 and mesolink.isconnector:
                mesolink.geometry_list_original_type = mesolink.geometry_list_no_lane_offset
            else:
                mesolink.geometry_list_original_type = mesolink.geometry_list
        for micronode in net_generator.micro_node_list:
            if not micronode.valid: continue
            micronode.x_coord_original_type, micronode.y_coord_original_type = micronode.x_coord, micronode.y_coord
    elif macro_net.coordinate_type == 'll':
        print('Converting coordiantes back to latlon')
        for node in macro_net.node_list:
            if not node.valid: continue
            y_coord, x_coord = macro_net.coord_convertor.to_latlon(node.x_coord, node.y_coord)
            node.y_coord_original_type, node.x_coord_original_type = round(y_coord,5), round(x_coord,5)
        for link in macro_net.link_list:
            if not link.valid: continue
            for point in link.geometry_list:
                y_coord, x_coord = macro_net.coord_convertor.to_latlon(point[0], point[1])
                link.geometry_list_original_type.append((round(x_coord,5), round(y_coord,5)))
        for mesonode in net_generator.meso_node_list:
            if not mesonode.valid: continue
            y_coord, x_coord = macro_net.coord_convertor.to_latlon(mesonode.x_coord, mesonode.y_coord)
            mesonode.y_coord_original_type, mesonode.x_coord_original_type = round(y_coord,5), round(x_coord,5)
        for mesolink in net_generator.meso_link_list:
            if not mesolink.valid: continue
            if connector_geometry_for_output == 2 and mesolink.isconnector:
                geometry_list = mesolink.geometry_list_no_lane_offset
            else:
                geometry_list = mesolink.geometry_list
            for point in geometry_list:
                y_coord, x_coord = macro_net.coord_convertor.to_latlon(point[0], point[1])
                mesolink.geometry_list_original_type.append((round(x_coord, 5), round(y_coord, 5)))
        for micronode in net_generator.micro_node_list:
            if not micronode.valid: continue
            y_coord, x_coord = macro_net.coord_convertor.to_latlon(micronode.x_coord, micronode.y_coord)
            micronode.y_coord_original_type, micronode.x_coord_original_type = round(y_coord,5), round(x_coord,5)
    elif macro_net.coordinate_type == 'f':
        print('Converting coordiantes back to feet')
        for node in macro_net.node_list:
            if not node.valid: continue
            node.x_coord_original_type, node.y_coord_original_type = node.x_coord * 3.2808, node.y_coord * 3.2808
        for link in macro_net.link_list:
            if not link.valid: continue
            for point in link.geometry_list:
                x_coord, y_coord = point[0] * 3.2808, point[1] * 3.2808
                link.geometry_list_original_type.append((x_coord, y_coord))
        for mesonode in net_generator.meso_node_list:
            if not mesonode.valid: continue
            mesonode.x_coord_original_type, mesonode.y_coord_original_type = mesonode.x_coord * 3.2808, mesonode.y_coord * 3.2808
        for mesolink in net_generator.meso_link_list:
            if not mesolink.valid: continue
            if connector_geometry_for_output == 2 and mesolink.isconnector:
                geometry_list = mesolink.geometry_list_no_lane_offset
            else:
                geometry_list = mesolink.geometry_list
            for point in geometry_list:
                x_coord, y_coord = point[0] * 3.2808, point[1] * 3.2808
                mesolink.geometry_list_original_type.append((x_coord, y_coord))
        for micronode in net_generator.micro_node_list:
            if not micronode.valid: continue
            micronode.x_coord_original_type, micronode.y_coord_original_type = micronode.x_coord * 3.2808, micronode.y_coord * 3.2808


def outputNetworks(macro_net, net_generator,connector_geometry_for_output):
    # convert coordinate from meter to the original type
    if connector_geometry_for_output in [1,2]:
        connector_geometry_for_output_ = connector_geometry_for_output
    else:
        print('please select \'connector_geometry_for_output\' from [1,2], default value 2 is used')
        connector_geometry_for_output_ = 2

    coordinateBack(macro_net, net_generator,connector_geometry_for_output_)

    print('Output networks...')
    # macro network
    macro_net_folder = os.path.join(macro_net.working_directory,'macronet')
    if not os.path.isdir(macro_net_folder): os.makedirs(macro_net_folder)
    with open(os.path.join(macro_net_folder,'node.csv'), 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['node_id','name','x_coord','y_coord','z_coord','node_type','ctrl_type','zone_id','activity_type','is_boundary'])
        for node in macro_net.node_list:
            if not node.valid: continue
            is_boundary = 1 if node.is_boundary else 0
            line = [node.node_id, node.name, node.x_coord_original_type, node.y_coord_original_type, '', '','', node.zone_id,node.activity_type,is_boundary]
            writer.writerow(line)
    with open(os.path.join(macro_net_folder,'link.csv'), 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['name','link_id','from_node_id','to_node_id','facility_type','dir_flag','length','lanes',
                         'capacity','free_speed','link_type','cost','geometry','TMC'])
        for link in macro_net.link_list:
            if not link.valid:continue
            geometry_str = 'LINESTRING ('
            for point in link.geometry_list_original_type:
                geometry_str += '{} {},'.format(point[0],point[1])
            geometry_str = geometry_str[:-1] + ')'
            line = ['',link.link_id, link.from_node_id, link.to_node_id, '','',link.coord_length,link.number_of_lanes,
                    link.lane_cap,link.speed_limit,link.link_type,'',geometry_str,link.TMC]
            writer.writerow(line)
    # with open(os.path.join(macro_net_folder,'main_node.csv'), 'w', newline='') as outfile:
    #     writer = csv.writer(outfile)
    #     writer.writerow(['main_node_id', 'new_node_id', 'original_nodes'])
    #     for main_node_id, new_node in macro_net.main_node_id_to_node_dict.items():
    #         original_nodes_str = ''
    #         for subnode in macro_net.main_node_id_to_subnode_list_dict[main_node_id]: original_nodes_str += '{};'.format(subnode.node_id)
    #         line = [main_node_id, new_node.node_id, original_nodes_str]
    #         writer.writerow(line)

    # meso network
    meso_net_folder = os.path.join(macro_net.working_directory,'mesonet')
    if not os.path.isdir(meso_net_folder): os.makedirs(meso_net_folder)
    with open(os.path.join(meso_net_folder,'node.csv'), 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['node_id','zone_id','x_coord','y_coord','original_node_id','activity_type','is_boundary'])
        for mesonode in net_generator.meso_node_list:
            if not mesonode.valid: continue
            is_boundary = 1 if mesonode.is_boundary else 0
            line = [mesonode.node_id, mesonode.zone_id,mesonode.x_coord_original_type, mesonode.y_coord_original_type, mesonode.original_node_id,mesonode.activity_type,is_boundary]
            writer.writerow(line)

    with open(os.path.join(meso_net_folder,'link.csv'), 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['link_id','from_node_id','to_node_id','facility_type','dir_flag','length','lanes','capacity',
                         'free_speed','link_type','cost','geometry','original_link_id','main_node_id','movement_str','TMC'])
        for mesolink in net_generator.meso_link_list:
            if not mesolink.valid: continue
            geometry_str = 'LINESTRING ('
            for point in mesolink.geometry_list_original_type:
                geometry_str += '{} {},'.format(point[0],point[1])
            geometry_str = geometry_str[:-1] + ')'
            original_link_id = mesolink.original_link_id if mesolink.original_link_id != -1 else None
            main_node_id = mesolink.main_node_id if mesolink.main_node_id != -1 else None
            line = [mesolink.link_id, mesolink.from_node_id, mesolink.to_node_id, '','',mesolink.length,
                    mesolink.number_of_lanes, mesolink.lane_cap,mesolink.speed_limit,mesolink.link_type,'',
                    geometry_str, original_link_id, main_node_id, mesolink.movement_str, mesolink.TMC]
            writer.writerow(line)

    # micro network
    micro_net_folder = os.path.join(macro_net.working_directory,'micronet')
    if not os.path.isdir(micro_net_folder): os.makedirs(micro_net_folder)   
    with open(os.path.join(micro_net_folder,'node.csv'), 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['node_id','x_coord','y_coord','meso_link_id','lane_no'])
        for micronode in net_generator.micro_node_list:
            if not micronode.valid: continue
            line = [micronode.node_id, micronode.x_coord_original_type, micronode.y_coord_original_type, micronode.meso_link_id, micronode.lane_no]
            writer.writerow(line)

    with open(os.path.join(micro_net_folder,'link.csv'), 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['link_id','from_node_id','to_node_id','facility_type','dir_flag','length','lanes','capacity',
                         'free_speed','link_type','cost','geometry','meso_link_id','cell_type','additional_cost','movement_str'])
        for microlink in net_generator.micro_link_list:
            if not microlink.valid: continue
            from_node = net_generator.micro_node_list[net_generator.micro_node_id_to_seq_no_dict[microlink.from_node_id]]
            to_node = net_generator.micro_node_list[net_generator.micro_node_id_to_seq_no_dict[microlink.to_node_id]]
            geometry_str = f'LINESTRING ({from_node.x_coord_original_type} {from_node.y_coord_original_type}, ' \
                           f'{to_node.x_coord_original_type} {to_node.y_coord_original_type})'
            line = [microlink.link_id, microlink.from_node_id, microlink.to_node_id,'','',microlink.length,1,'',microlink.speed_limit,
                    '','',geometry_str, microlink.meso_link_id,microlink.cell_type,microlink.additional_cost,microlink.movement_str]
            writer.writerow(line)

    if net_generator.qa is None: return
    meso_net2_folder = os.path.join(macro_net.working_directory,'mesonet2')
    if not os.path.isdir(meso_net2_folder): os.makedirs(meso_net2_folder)
    with open(os.path.join(meso_net2_folder,'node.csv'), 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['node_id','zone_id','x_coord','y_coord','original_node_id'])
        for mesonode in net_generator.qa.meso_node_list:
            if not mesonode.valid: continue
            line = [mesonode.node_id, mesonode.zone_id,mesonode.x_coord, mesonode.y_coord, mesonode.original_node_id]
            writer.writerow(line)

    with open(os.path.join(meso_net2_folder,'road_link.csv'), 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['road_link_id','from_node_id','to_node_id','facility_type','dir_flag','length','lanes','capacity',
                         'free_speed','link_type','cost','geometry','original_link_id','main_node_id','movement_str'])
        for mesolink in net_generator.qa.meso_link_list:
            if not mesolink.valid: continue
            geometry_str = 'LINESTRING ('
            for point in mesolink.geometry_list: geometry_str += '{} {},'.format(point[0],point[1])
            for point in mesolink.geometry_list: geometry_str += '{} {},'.format(point[0],point[1])
            geometry_str = geometry_str[:-1] + ')'
            original_link_id = mesolink.original_link_id if mesolink.original_link_id != -1 else None
            main_node_id = mesolink.main_node_id if mesolink.main_node_id != -1 else None
            # movement_str = mesolink.movement_str if mesolink.movement_str_output else None
            line = [mesolink.link_id, mesolink.from_node_id, mesolink.to_node_id, '','',mesolink.length, mesolink.number_of_lanes,
                    mesolink.lane_cap,mesolink.speed_limit,'','', geometry_str, original_link_id, main_node_id,
                    mesolink.movement_str]
            writer.writerow(line)

    micro_net2_folder = os.path.join(macro_net.working_directory,'micronet2')
    if not os.path.isdir(micro_net2_folder): os.makedirs(micro_net2_folder)
    with open(os.path.join(micro_net2_folder,'node.csv'), 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['node_id','x_coord','y_coord','meso_link_id','lane_no'])
        for micronode in net_generator.qa.micro_node_list:
            if not micronode.valid: continue
            line = [micronode.node_id, micronode.x_coord, micronode.y_coord, micronode.meso_link_id, micronode.lane_no]
            writer.writerow(line)

    with open(os.path.join(micro_net2_folder,'road_link.csv'), 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['road_link_id','from_node_id','to_node_id','facility_type','dir_flag','length','lanes','capacity',
                         'free_speed','link_type','cost','meso_link_id','cell_type','additional_cost'])
        for microlink in net_generator.qa.micro_link_list:
            if not microlink.valid: continue
            line = [microlink.link_id, microlink.from_node_id, microlink.to_node_id,'','',microlink.length,1,'',microlink.speed_limit,
                    '','',microlink.meso_link_id,microlink.cell_type,microlink.additional_cost]
            writer.writerow(line)