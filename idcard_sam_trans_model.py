# 
# tool _> tpu reset
# tool <_ tpu 
# tool _> tpu init (tool模拟一种设备)
# tool <_ tpu
# for
# tool _> tpu type b search
# tool <_ tpu (可能没有，循环等待)
# end
# for
# SAM <_> tool <_> tpu
# end
graph = [
    # 两个设备初始化
    {
        'type':'init_com'
        ,'id':'sam'
        ,'in': {
            'baudrate':'115200'
            ,'parity':'N'
            ,'port':'COM5'
        }
        ,'out':'out_sam'
        ,'prev':'start' # 标记起始
        ,'next':'tpu'
    }
    ,{
        'type':'init_com'
        ,'id':'tpu'
        ,'in':{
            'baudrate':'115200'
            ,'parity':'N'
            ,'port':'COM6'
        }
        ,'out':'out_tpu'
        ,'prev':'sam'
        ,'next':'tpu_read'
    }
    # tpu读状态
    ,{
        'type':'constant'
        ,'id':'tpu_read_code'
        # 给tpu的数据，只写内容报文，校验和包头包尾可以使用preRun的pack_tpu自动添加
        ,'data':[0x04,0x00,0x21,0x53,0x02,0x00]
    }
    ,{
        'type':'com_node'
        ,'id':'tpu_read'
        ,'dev':'out_tpu'
        ,'in': 'tpu_read_code'
        ,'preRun':['pack_tpu']
        ,'postRun':['unpack_tpu']
        ,'out':'tpu_status'
        ,'prev':'sam'
        ,'next':'tpu_status_extract'
    }
    # tpu状态提取
    ,{
        'type':'byte_extract'
        ,'id':'tpu_status_extract'
        ,'in':'tpu_status'
        ,'offset':6
        ,'out':'tpu_status_short'
        ,'prev':'tpu_read'
        ,'next':'tpu_status_condition'
    }
    # 状态判断和跳转
    ,{
        'type':'const_condition_node'
        ,'id':'tpu_status_condition'
        ,'in':'tpu_status_short'
        ,'out':'tpu_status_id'
        ,'prev':'tpu_read'
        ,'next':{
            'FF':'tpu_reset'
            ,'FE':'tpu_init'
            ,'00':'tpu_read_bcard'
            ,'01':'tpu_reset'
        }
    }
    # tpu复位命令及运行
    ,{
        'type':'constant'
        ,'id':'tpu_reset_code'
        ,'data':[0x04,0x00,0x02,0x53,0x00,0x00]
    }
    ,{
        'type':'com_node'
        ,'id':'tpu_reset'
        ,'dev':'out_tpu'
        ,'in': 'tpu_reset_code'
        ,'preRun':['pack_tpu']
        ,'out':'out_tpu1'
        ,'prev':'tpu_status_condition'
        ,'next':'tpu_init'
        ,'out_policy':{
            'timeout':5.0
        }
    }
    # tpu初始化命令及运行
    ,{
        'type':'constant'
        ,'id':'tpu_init_code'
        ,'data':[0x02,0x31,0x00,0x01,0x53,0x00,0x00,0x00,0x00,0x00,0x10,0x02,0x17,0x59,0x01,0x3B,0x10,0x02,0x3B,0x11,0x00,0x09,0x39,0x00,0x00,0x00,0x20,0x22,0x07,0x05,0x20,0x22,0x07,0x05,0x00,0x01,0x00,0x33,0x33,0x33,0x00,0x11,0x10,0x03,0x00,0x05,0x00,0x10,0x03,0x00,0x01,0x00,0x00,0x00,0x00,0x00,0x2A,0x03]
    }
    ,{
        'type':'com_node'
        ,'id':'tpu_init'
        ,'dev':'out_tpu'
        ,'in':'tpu_init_code'
        ,'out':'out_tpu2'
        ,'prev':['tpu_status_condition','tpu_reset']
        ,'next':'tpu_read_bcard'
    }
    # tpu 寻type-b卡
    ,{
        'type':'constant'
        ,'id':'tpu_typeb_code'
        ,'data':[0x0C,0x00,0x31,0x54,0x00,0x01,0x00,0x20,0x22,0x07,0x05,0x13,0x39,0x08]
    }
    ,{
        'type':'com_node'
        ,'id':'tpu_read_bcard'
        ,'dev':'out_tpu'
        ,'in': 'tpu_typeb_code'
        ,'preRun':['pack_tpu']
        ,'postRun':['unpack_tpu']
        ,'out':'b_card_status'
        ,'prev':['tpu_status_condition','tpu_init']
        ,'next':'b_card_status_extract'
    }
    # 读卡状态提取
    ,{
        'type':'byte_extract'
        ,'id':'b_card_status_extract'
        ,'in':'b_card_status'
        ,'offset':5
        ,'out':'b_card_status_short'
        ,'prev':'tpu_read_bcard'
        ,'next':'b_card_status_condition'
    }
    # 读卡状态判断和跳转
    ,{
        'type':'const_condition_node'
        ,'id':'b_card_status_condition'
        ,'in':'b_card_status_short'
        ,'out':'bcard_status_id'
        ,'prev':'b_card_status_extract'
        ,'next':{
            '00':'round_info'
            ,'01':'tpu_read_bcard'
        }
    }
    # 发SAM命令,第一次是固定的
    ,{
        'type':'constant'
        ,'id':'command_to_sam'
        ,'data':[0x02,0x00,0x00,0x00,0x1c,0x80,0x00,0x00,0x00,0x12,0x00,0x00,0x3c,0x00,0x00,0xbe,0x99,0x00,0x00,0x00,0x0c,0x50,0x00,0x00,0x00,0x00,0xd1,0x03,0x86,0x07,0x00,0x80,0x90,0x8a,0x03]
    }
    ,{
        'type':'variable'
        ,'id':'round_var'
        ,'data':0
    }
    ,{
        'type':'info_node'
        ,'id':'round_info'
        ,'in':'round_var'
        ,'out':'round_var'
        ,'preRun':['incr']
        ,'prev':['b_card_status_condition','send_to_tpu']
        ,'next':'send_to_sam'
    }
    ,{
        'type':'com_node'
        ,'id':'send_to_sam'
        ,'dev':'out_sam'
        ,'in': 'command_to_sam'
        # ,'preRun':['log']
        # ,'postRun':['log']
        ,'out':'recv_from_sam'
        ,'prev':'b_card_status_condition'
        ,'next':'sam_output_extract'
        ,'out_policy': {
            'timeout':2.0
            ,'type':'stx_multi_length'
            ,'escape':None
            ,'length_map':{
                0xDD:{
                    # 去除首字节后的下标,额外长度
                    'begin':0
                    ,'end':2
                    ,'basic_len':0
                }
                ,0x02:{
                    # 去除首字节后的下标
                    'begin':0
                    ,'end':4
                    ,'basic_len':2
                }
            }
        }
    }
    # 提取首字节用于判断是否完成通信
    ,{
        'type':'byte_extract'
        ,'id':'sam_output_extract'
        ,'in':'recv_from_sam'
        ,'offset':0
        ,'out':'recv_from_sam_short'
        ,'prev':'send_to_sam'
        ,'next':'tpu_sam_condition'
    }
    # sam返回状态判断和跳转
    ,{
        'type':'const_condition_node'
        ,'id':'tpu_sam_condition'
        ,'in':'recv_from_sam_short'
        ,'out':'sam_tpu_status_id'
        ,'prev':'sam_output_extract'
        ,'next':{
            'DD':'send_to_tpu' # 判断条件目前是大小写敏感的
            ,'02':'end'
        }
    }
    # sam数据发到tpu
    ,{
        'type':'com_node'
        ,'id':'send_to_tpu'
        ,'dev':'out_tpu'
        ,'in': 'recv_from_sam'
        # ,'preRun':['log','sam_to_tpu','log','pack_tpu','log'] # 按顺序执行各个预处理
        # ,'postRun':['log','unpack_tpu','log','tpu_to_sam','log'] # 按顺序执行各个后处理
        ,'preRun':['sam_to_tpu','pack_tpu'] # 按顺序执行各个预处理
        ,'postRun':['unpack_tpu','tpu_to_sam'] # 按顺序执行各个后处理
        ,'out':'command_to_sam'
        ,'prev':'tpu_sam_condition'
        ,'out_policy': {
            'timeout':2.0
            ,'type':'border'
            ,'begin':0x02
            ,'end':0x03
            # 转义字符
            ,'escape':0x10
        }
        ,'next':'round_info'
    }
]

tpu_readb_graph = [
    {
        'type':'init_com'
        ,'id':'tpu'
        ,'in':{
            'baudrate':'115200'
            ,'parity':'N'
            ,'port':'COM5'
        }
        ,'out':'out_tpu'
        ,'prev':'sam'
        ,'next':'tpu_read'
    }
    # tpu读状态
    ,{
        'type':'constant'
        ,'id':'tpu_read_code'
        # 给tpu的数据，只写内容报文，校验和包头包尾可以使用preRun的pack_tpu自动添加
        ,'data':[0x04,0x00,0x21,0x53,0x02,0x00]
    }
    ,{
        'type':'com_node'
        ,'id':'tpu_read'
        ,'dev':'out_tpu'
        ,'in': 'tpu_read_code'
        ,'preRun':['pack_tpu']
        ,'postRun':['unpack_tpu']
        ,'out':'tpu_status'
        ,'prev':'sam'
        ,'next':'tpu_status_extract'
    }
    # tpu状态提取
    ,{
        'type':'byte_extract'
        ,'id':'tpu_status_extract'
        ,'in':'tpu_status'
        ,'offset':6
        ,'out':'tpu_status_short'
        ,'prev':'tpu_read'
        ,'next':'tpu_status_condition'
    }
    # 状态判断和跳转
    ,{
        'type':'const_condition_node'
        ,'id':'tpu_status_condition'
        ,'in':'tpu_status_short'
        ,'out':'tpu_status_id'
        ,'prev':'tpu_read'
        ,'next':{
            'FF':'tpu_reset'
            ,'FE':'tpu_init'
            ,'00':'tpu_read_bcard'
            ,'01':'tpu_reset'
        }
    }
    # tpu复位命令及运行
    ,{
        'type':'constant'
        ,'id':'tpu_reset_code'
        ,'data':[0x04,0x00,0x02,0x53,0x00,0x00]
    }
    ,{
        'type':'com_node'
        ,'id':'tpu_reset'
        ,'dev':'out_tpu'
        ,'in': 'tpu_reset_code'
        ,'preRun':['pack_tpu']
        ,'out':'out_tpu1'
        ,'prev':'tpu_status_condition'
        ,'next':'tpu_init'
        ,'out_policy':{
            'timeout':5.0
        }
    }
    # tpu初始化命令及运行
    ,{
        'type':'constant'
        ,'id':'tpu_init_code'
        ,'data':[0x02,0x31,0x00,0x01,0x53,0x00,0x00,0x00,0x00,0x00,0x10,0x02,0x17,0x59,0x01,0x3B,0x10,0x02,0x3B,0x11,0x00,0x09,0x39,0x00,0x00,0x00,0x20,0x22,0x07,0x05,0x20,0x22,0x07,0x05,0x00,0x01,0x00,0x33,0x33,0x33,0x00,0x11,0x10,0x03,0x00,0x05,0x00,0x10,0x03,0x00,0x01,0x00,0x00,0x00,0x00,0x00,0x2A,0x03]
    }
    ,{
        'type':'com_node'
        ,'id':'tpu_init'
        ,'dev':'out_tpu'
        ,'in':'tpu_init_code'
        ,'out':'out_tpu2'
        ,'prev':['tpu_status_condition','tpu_reset']
        ,'next':'tpu_read_bcard'
    }
    # tpu 寻type-b卡
    ,{
        'type':'constant'
        ,'id':'tpu_typeb_code'
        ,'data':[0x0C,0x00,0x31,0x54,0x00,0x01,0x00,0x20,0x22,0x07,0x05,0x13,0x39,0x08]
    }
    ,{
        'type':'com_node'
        ,'id':'tpu_read_bcard'
        ,'dev':'out_tpu'
        ,'in': 'tpu_typeb_code'
        ,'preRun':['pack_tpu']
        ,'postRun':['unpack_tpu']
        ,'out':'b_card_status'
        ,'prev':['tpu_status_condition','tpu_init']
        ,'next':'b_card_status_extract'
    }
    # 读卡状态提取
    ,{
        'type':'byte_extract'
        ,'id':'b_card_status_extract'
        ,'in':'b_card_status'
        ,'offset':5
        ,'out':'b_card_status_short'
        ,'prev':'tpu_read_bcard'
        ,'next':'b_card_status_condition'
    }
    # 读卡状态判断和跳转
    ,{
        'type':'const_condition_node'
        ,'id':'b_card_status_condition'
        ,'in':'b_card_status_short'
        ,'out':'bcard_status_id'
        ,'prev':'b_card_status_extract'
        ,'next':{
            '01':'send_to_sam'
            ,'00':'tpu_read_bcard'
        }
    }
]