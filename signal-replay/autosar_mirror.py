import struct
import time

class AutosarMirror:

    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.protocol_version = 1
         # 仅第一次为1，只有当源总线的状态自上次被报告以来发生变化时，它才会出现
        self.network_state_available = 1
        # 当报告源总线状态改变时，FrameID可以被省略
        self.frame_id_available = 1
        # 当报告源总线状态改变时，FrameID可以被省略
        self.payload_available = 1
        self.network_type = 0b00100
        self.network_id = 1
        # Frames Lost + Bus Online State + Error-Passive state + Bus-Off + Tx error counter
        # Frames Lost: 当一个或多个通过过滤器的源帧，因为目的总线的队列满或传输失败而丢失后，帧丢失状态应该被设置为1。接着再次设置为0。
        # Bus Online State: 当源总线在线时，即控制器和收发器都能通信时，总线在线状态设置为1。否则设置为0
        # Error-Passive state: 当CAN控制器处于错误被动状态（Error-Passive state）时，应将无错误状态设置为1。当它处于错误主动（Error-Active）或Bus-Off状态时，值为0
        # Bus-Off: 当CAN控制器处于Bus-Off状态时，Bus-Off状态应设置为1，当CAN控制器处于主动错误（Error-Active）或被动错误（Error-Passive）状态时，Bus-Off状态应设置为0
        # Tx error counter: 数值位Tx错误计算除以8
        self.network_state_can = 0b01010000
        self.data: bytes = bytes()
        self.data_length = 0
        self.sequence_number = 0
    
    def append_data(self, msg):
            # 时间偏移量
            time_diff = int((msg.timestamp - self.timestamp)*100000).to_bytes(2, byteorder='big')
            # 网络状态有效位 + FlameID有效位 + Payload有效位 + 网络类型
            available_byte = (self.network_state_available << 7) | (self.frame_id_available << 6) | (self.payload_available << 5) | self.network_type
            available_byte = available_byte.to_bytes(1, byteorder='big')
            if(self.network_state_available == 1):
                self.network_state_available = 0
            network_id = self.network_id.to_bytes(1, byteorder='big')
            data = time_diff + available_byte + network_id
            if self.network_state_available == 1:
                data += self.network_state_can
            if self.frame_id_available == 1:
                # CAN ID类型: 对于扩展CAN ID（Extended CAN ID），第0字节的第7位应该设置为1，对于标准CAN ID （Standard CAN ID），应该设置为0。
                can_id = 0
                if msg.is_extended_id:
                    can_id = 1
                # CAN FD: 对应CAN FD帧格式设置为1，对于CAB 2.0帧应该设置为0
                can_fd = 0
                if msg.is_fd:
                    can_fd = 1
                # CAN ID类型 + CAN FD + 保留位0 + CAN ID
                frame_id = ((can_id << 31) | (can_fd << 30) | (0 << 29) | msg.arbitration_id) & 0xFFFFFFFF
                data += frame_id.to_bytes(4, byteorder='big')
            if self.payload_available == 1:
                self.data_length += msg.dlc
                payload_length = msg.dlc.to_bytes(1, byteorder='big')
                data += payload_length + msg.data
            self.data += data
            return len(self.data)

    def build_header(self):
        protocol_version = self.protocol_version.to_bytes(1, byteorder='big')
        self.sequence_number = (self.sequence_number + 1) % 256
        timestamp_second = int(self.timestamp)
        timestamp_nano = int((self.timestamp - timestamp_second) * 1000000)
        timestamp_second = timestamp_second.to_bytes(6, byteorder='big')
        timestamp_nano = timestamp_nano.to_bytes(4, byteorder='big')
        header = protocol_version + \
                 self.sequence_number.to_bytes(1, byteorder='big') + \
                 timestamp_second + \
                 timestamp_nano + \
                 self.data_length.to_bytes(2, byteorder='big')
        return header
    
    def to_data(self):
        header = self.build_header() 
        hex_header = ''.join(['{:02X}'.format(b) for b in header])
        print("header:", hex_header, len(header))
        hex_data = ''.join(['{:02X}'.format(b) for b in self.data])
        print("data:", hex_data, len(self.data))
        return header + self.data
    
    
