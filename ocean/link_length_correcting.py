# @author       Jiawei Lu
# @email        jiaweil9@asu.edu
# @create date  2020/04/25 13:22
# @desc         [description]

import pandas as pd
import re


link_data = pd.read_csv(r'..\Datasets\Beijing-Net\road_link.csv')

def getCoordLength(geometry_str):
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
    return coord_length



link_data['length_new'] = link_data['geometry'].apply(getCoordLength)
link_data.to_csv(r'..\Datasets\Beijing-Net\road_link_new.csv', index=False)

