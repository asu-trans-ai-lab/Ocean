# @author        Jiawei Lu
# @email         jiaweil9@asu.edu
# @create date   2020-04-16 17:18:07
# @desc          [description]


class CMesoNode:
    def __init__(self):
        self.name = ''
        self.node_id = 0
        self.node_seq_no = 0
        self.iszone = False
        self.zone_id = None
        self.control_type = -1
        self.control_type_name = ''
        self.cycle_length_in_second = 0
        self.x_coord = 0.0
        self.y_coord = 0.0
        self.m_outgoing_link_list = []
        self.m_incoming_link_list = []

        self.original_node_id = None
        self.valid = True

        self.x_coord_original_type = 0.0
        self.y_coord_original_type = 0.0

        self.activity_type = ''
        self.is_boundary = False


class CMesoLink:
    def __init__(self):
        self.name = ''
        self.link_id = 0
        self.link_seq_no = 0
        self.from_node_id = 0
        self.to_node_id = 0
        self.link_type = 0
        self.TMC = ''
        self.length = 0.0
        self.length_in_km = 0.0
        self.number_of_lanes = 0
        self.number_of_lanes_of_original_link = 0
        self.changes_of_lanes = []
        self.speed_limit = 0.0
        self.lane_cap = 0.0
        self.flow_volume = 0.0
        self.BPR_alpha = 0.15
        self.BPR_beta = 4.0
        self.link_capacity = 0.0
        self.travel_time = 0.0
        self.cost = 0.0
        
        self.link_key = ''
        self.isconnector = False
        self.geometry_list = []             # list<float*> geometry_list;
        self.geometry_list_no_lane_offset = []
        
        self.micro_node_list = []           # list<list<int>> micro_node_set;			//micro node id, lane by lane;
        self.micro_link_list = []           # list<int> micro_link_set;			//micro link id;
                
        self.micro_incoming_node_id_list = None
        self.micro_outgoing_node_id_list = None
        self.turning_node_seq_no_dict = {}      # std::map<int, list<int>> turning_node_seq_no_dict;             //meso_link_seq_no:micro_node_seq_no
        self.estimated_cost_tree_for_each_movement = {}     # std::map<int, map<int,float>> estimated_cost_tree_for_each_movement;     //meso_link_seq_no : node_seq_no: cost

        self.section_lane_coord_list = []
        self.section_length_list = []
        self.section_cell_offset_list = []
        self.micro_node_id_list_for_each_section = []
        self.section_connection_node_id_list = []

        self.original_link_id = -1
        self.valid = True
        self.movement_str = ''
        # self.movement_str_output = False
        self.main_node_id = -1

        self.geometry_list_original_type = []
