import can
import socket
from autosar_mirror import AutosarMirror

# 解析BLF
blf_data = can.BLFReader("/can.blf")
tmp_data_length = 0
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

for msg in blf_data:
    if tmp_data_length == 0:
        autosarMirror = AutosarMirror(msg.timestamp)
    tmp_data_length = autosarMirror.append_data(msg)
    # 满500字节则发送一个数据包
    if tmp_data_length > 500:
        sock.sendto(autosarMirror.to_data(), ("127.0.0.1", 5005))
        tmp_data_length = 0

