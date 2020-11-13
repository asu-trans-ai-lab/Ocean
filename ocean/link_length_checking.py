# @author       Jiawei Lu
# @email        jiaweil9@asu.edu
# @create date  2020/04/25 12:56
# @desc         [description]

import pandas as pd
import re


link_data = pd.read_csv(r'..\Datasets\Beijing-Net\road_link.csv')

number_of_records = len(link_data)
warning_info_list = []

for i in range(number_of_records):
    geometry_str = link_data.loc[i, 'geometry']
    length = link_data.loc[i, 'length'] * 1000
    link_id = link_data.loc[i, 'road_link_id']

    coord_str = re.findall(r'<LineString><coordinates>(.*)</coordinates></LineString>', geometry_str)[0]
    coord_str_list = coord_str.split(' ')
    geometry_list_temp = []
    for item in coord_str_list:
        coord_temp = item.split(',')[:2]
        geometry_list_temp.append(tuple(map(float, coord_temp)))

    geometry_list_temp_set = list(set(geometry_list_temp))
    if len(geometry_list_temp_set) != len(geometry_list_temp):
        geometry_list = geometry_list_temp_set.sort(key=geometry_list_temp.index)
    else:
        geometry_list = geometry_list_temp

    coord_length = 0
    for j in range(len(geometry_list) - 1):
        coord_length += ((geometry_list[j + 1][0] - geometry_list[j][0]) ** 2 + (
                    geometry_list[j + 1][1] - geometry_list[j][1]) ** 2) ** 0.5


    if abs(coord_length - length) / length > 0.2:
        warning_info = 'warning: link id: {}, link length inconsistency detected. link length {}, coordinate length {}\n'.format(
                link_id, length, coord_length)
        warning_info_list.append(warning_info)

with open(r'..\Datasets\Beijing-Net\warning.txt','w') as fin:
    fin.writelines(warning_info_list)