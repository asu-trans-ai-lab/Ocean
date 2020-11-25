# @author        Jiawei Lu
# @email         jiaweil9@asu.edu
# @create date   2020-04-16 17:51:42
# @desc          [description]


class CMicroNode:
    def __init__(self):
        self.node_id = 0
        self.node_seq_no = 0
        self.x_coord = 0.0
        self.y_coord = 0.0
        self.meso_link_id = 0
        self.lane_no = 0
        self.m_outgoing_link_list = []
        self.m_incoming_link_list = []
        self.available_sim_interval = 0

        self.valid = True
        self.x_coord_original_type = 0.0
        self.y_coord_original_type = 0.0

        self.activity_type = ''
        self.is_boundary = None


class CMicroLink:
    def __init__(self):
        self.link_id = 0
        self.link_seq_no = 0
        self.from_node_id = 0
        self.to_node_id = 0
        self.meso_link_id = 0
        self.lane_no = 0
        self.length = 0.0
        self.speed_limit = 0.0
        self.free_flow_travel_time_in_min = 0.0
        self.free_flow_travel_time_in_simu_interval = 0
        self.additional_cost = 0.0
        self.cost = 0.0
        self.cell_type = 1	            # //1:traveling; 2:changing

        self.valid = True
        self.movement_str = ''