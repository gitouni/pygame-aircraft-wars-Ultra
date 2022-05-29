import json
import socket
from enum import Enum
import threading
import time
from math import isnan
import utils

class NetType(Enum):
    Client = 0
    Server = 1

class Protocol(Enum):
    SEND_NET_STATE = 0
    SEND_MESSAGE = 1
    SEND_GAME_STATE = 2
    RECEIVE_MESSAGE = 3


class Client:
    def __init__(self,host:str,port:int,timeout:float=5.0,max_wait_time:float=1.0):
        self.meta = dict(host=host,port=port,timeout=timeout,max_wait_time=max_wait_time)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_open = False
        self.content_buff = []
        self.log_buff = []
        self.open_lock = threading.Lock()
        self.content_lock = threading.Lock()
        self.log_lock = threading.Lock()
    def init_connect(self)->bool:
        if self.is_open:
            return True
        try:
            self.client.settimeout(self.meta['timeout'])
            self.client.connect((self.meta['host'],self.meta['port']))
            self.is_open = True
            with self.log_lock:
                self.log_buff.append(utils.msg_with_time('Connction Established.'))
            return True
        except socket.timeout:
            with self.log_lock:
                self.log_buff.append(utils.msg_with_time('Connction Time out.'))
            return False
        except ConnectionRefusedError or ConnectionAbortedError:
            with self.log_lock:
                self.log_buff.append(utils.msg_with_time('Connction Refused.'))
            return False
        
    def open(self):
        with self.open_lock:
            self.is_open = self.init_connect()
    
    def close(self):
        self.client.close()
        with self.log_lock:
            self.log_buff.append(utils.msg_with_time('Connection closed normally.'))
        self.is_open = False
        
    def send_msg(self,msg:str):
        if not self.is_open:
            with self.log_lock:
                self.log_buff.append(utils.msg_with_time('Reject to send, disconnected with server!'))
            return
        data = dict(type=Protocol.SEND_MESSAGE.value,content=msg)
        data_str = json.dumps(data)
        self.client.send(data_str.encode('utf-8'))
        with self.log_lock:
            self.log_buff.append(utils.msg_with_time('Message has been sent to server {}.'.format(self.meta['host'])))
        
    def mesaure_msg(self,cnt=10):
        data = dict(type=Protocol.SEND_MESSAGE.value,content='request for delay')
        data_str = json.dumps(data)
        for _ in range(cnt):
            start_time = time.time()
            self.client.sendall(data_str.encode('utf-8'))
            try:
                rev_data_str = self.client.recv(1024).decode('utf-8')
                while rev_data_str == '':
                    rev_data_str = self.client.recv(1024).decode('utf-8')
                    if time.time() - start_time > self.meta['max_wait_time']:
                        print('excceed maximum waiting time, close connection')
                        break
                print(rev_data_str)
            except socket.timeout:
                print('connection timeout')
                return
            

        # 平均延迟，丢包率
    def measure_delay(self,cnt=10):
        data = dict(type=Protocol.SEND_NET_STATE.value,content='request for delay')
        data_str = json.dumps(data)
        total_time = 0.0
        total_rev_packs = 0
        for _ in range(cnt):
            flag = True
            start_time = time.time()
            self.client.sendall(data_str.encode('utf-8'))
            try:
                rev_data_str = self.client.recv(1024).decode('utf-8')
            except socket.timeout:
                return float('nan'), 0
            while rev_data_str == '':
                rev_data_str = self.client.recv(1024).decode('utf-8')
                if time.time() - start_time > self.meta['max_wait_time']:
                    flag = False
                    break
            if flag:
                total_time += time.time() - start_time
                total_rev_packs += 1
        # 平均延迟，丢包率
        if total_rev_packs == 0:
            return float('nan'), 0
        else:
            return total_time/total_rev_packs, total_rev_packs/cnt
        
    def msg_rev_thread(self):
        while True:
            with self.open_lock:
                is_open = self.is_open
            if not is_open:
                break
            try:
                while True:
                    try:
                        buff_str = self.client.recv(1024).decode('utf-8')
                    except socket.timeout:
                        buff_str = ""
                        with self.log_lock:
                            self.log_buff.append(utils.msg_with_time('None of messages received.'))
                    except OSError:
                        pass
                    if buff_str == "":  # 为空说明未收到任何数据，重新接收
                        continue
                    ## 以下为客户端的响应程序
                    buff = json.loads(buff_str)  # dict
                    if buff['type'] == Protocol.SEND_NET_STATE.value:  # 网络延迟测试    
                        data = dict(type=Protocol.SEND_NET_STATE.value,content='from {}'.format(self.meta['host']))
                        data_str = json.dumps(data)
                        self.client.send(data_str.encode('utf-8'))
                    elif buff['type'] == Protocol.SEND_MESSAGE.value:
                        data = dict(type=Protocol.RECEIVE_MESSAGE.value,content='Message Recieved!')
                        data_str = json.dumps(data)
                        self.client.send(data_str.encode('utf-8'))
                        with self.content_lock:
                            self.content_buff.append(utils.msg_with_time(buff['content']))
                    elif buff['type'] == Protocol.RECEIVE_MESSAGE.value:
                        with self.log_lock:
                            self.log_buff.append(utils.msg_with_time('Message Received'))
                    else:
                        data = dict(type=Protocol.SEND_NET_STATE.value,content='Unknown message received!')
                        data_str = json.dumps(data)
                        self.client.send(data_str.encode('utf-8'))
                        with self.log_lock:
                            self.log_buff.append(utils.msg_with_time('Unknown message recevied from {}'.format(self.meta['host'])))
            except ConnectionAbortedError:
                with self.log_lock:
                    self.log_buff.append(utils.msg_with_time('Disconnect with Server:{}'.format(self.meta['host'])))
                return

    
class Server:
    def __init__(self,host:str,port:int,timeout:float=5.0,closetime:float=1000):
        self.meta = dict(host=host,port=port,timeout=timeout,closetime=closetime)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_open = True
        self.content_buff = []
        self.log_buff = []
        self.open_lock = threading.Lock()
        self.content_lock = threading.Lock()
        self.log_lock = threading.Lock()
        self.ss = None
        self.ss_ip = None
    def init_bind(self):
        self.server.bind((self.meta['host'],self.meta['port']))
        self.server.settimeout(self.meta['timeout'])
        self.server.listen(5)
    def close(self):
        with self.open_lock:
            self.is_open = False
            self.ss = None
            self.server.close()
        with self.log_lock:
            self.log_buff.append(utils.msg_with_time('Connection closed normally.'))
    def open(self):
        with self.open_lock:
            self.is_open = True
            
    def send_msg(self,msg:str):
        if self.ss is None:
            with self.log_lock:
                self.log_buff.append(utils.msg_with_time('Reject to send, none of connected node!'))
        else:
            data = dict(type=Protocol.SEND_MESSAGE.value,content=msg)
            data_str = json.dumps(data)
            self.ss.send(data_str.encode('utf-8'))
            with self.log_lock:
                self.log_buff.append(utils.msg_with_time('Message has been sent to {}'.format(self.ss_ip)))
    def msg_rev_thread(self):
        serve_start = time.time()
        while time.time() - serve_start < self.meta['closetime']:
            with self.open_lock:
                if not self.is_open:
                    break
            try:
                self.ss, addr = self.server.accept()
                self.ss_ip = addr[0]
                with self.log_lock:
                    self.log_buff.append(utils.msg_with_time('Connection from: {}'.format(addr[0])))
                flag = True
                while flag:
                    if not self.is_open:
                        break
                    try:
                        while True:
                            try:
                                buff_str = self.ss.recv(1024).decode('utf-8')
                                if buff_str == "":  # 为空说明未收到任何数据，重新接收
                                    continue
                                ## 以下为服务端的响应程序
                                buff = json.loads(buff_str)  # dict
                                if buff['type'] == Protocol.SEND_NET_STATE.value:  # 网络延迟测试    
                                    data = dict(type=Protocol.SEND_NET_STATE.value,content='from {}'.format(addr))
                                    data_str = json.dumps(data)
                                    self.ss.send(data_str.encode('utf-8'))
                                elif buff['type'] == Protocol.SEND_MESSAGE.value:
                                    data = dict(type=Protocol.RECEIVE_MESSAGE.value,content='Message Recieved!')
                                    data_str = json.dumps(data)
                                    self.ss.send(data_str.encode('utf-8'))
                                    with self.content_lock:
                                        self.content_buff.append(utils.msg_with_time(buff['content']))
                                elif buff['type'] == Protocol.RECEIVE_MESSAGE.value:
                                    with self.log_lock:
                                        self.log_buff.append(utils.msg_with_time('Message Received'))
                                else:
                                    data = dict(type=Protocol.SEND_NET_STATE.value,content='Unknown message received!')
                                    data_str = json.dumps(data)
                                    self.ss.send(data_str.encode('utf-8'))
                                    with self.log_lock:
                                        self.log_buff.append(utils.msg_with_time('Unknown message recevied from {}'.format(addr[0])))
                            except ConnectionError:
                                flag = False
                                with self.log_lock:
                                    self.log_buff.append(utils.msg_with_time('Connection Error!'))
                                break
                            except AttributeError:
                                pass
                    except ConnectionAbortedError:
                        with self.log_lock:
                            self.log_buff.append(utils.msg_with_time('Connection offline:{}'.format(addr)))
                        return
            except socket.timeout:
                with self.log_lock:
                    self.log_buff.append(utils.msg_with_time("time out for connection, keep waiting for {:.1f}s".format(
                                    self.meta['closetime'] - time.time() + serve_start)))
                self.ss = None
                self.ss_ip = None
                pass
    def auto_serve(self):
        def serve_thread():
            serve_start = time.time()
            while time.time() - serve_start < self.meta['closetime']:
                try:
                    ss, addr = self.server.accept()
                    start_time = time.time()
                    flag = True
                    while flag:
                        try:
                            while True:
                                buff_str = ss.recv(1024).decode('utf-8')
                                if buff_str == "":  # 为空说明未收到任何数据，重新接收
                                    now = time.time()
                                    if now - start_time > self.meta['timeout']:
                                        print('Connection timeout:{}'.format(addr))
                                        ss.close()
                                        flag = False
                                        break
                                    else:
                                        # print(now - start_time)
                                        break
                                else:
                                    start_time = time.time()
                                ## 以下为服务端的响应程序
                                buff = json.loads(buff_str)  # dict
                                if buff['type'] == Protocol.SEND_NET_STATE.value:  # 网络延迟测试    
                                    data = dict(type=Protocol.SEND_NET_STATE.value,content='from {}'.format(addr))
                                    data_str = json.dumps(data)
                                    ss.send(data_str.encode('utf-8'))
                                elif buff['type'] == Protocol.SEND_MESSAGE.value:
                                    data = dict(type=Protocol.SEND_MESSAGE.value,content='Message Recieved!')
                                    data_str = json.dumps(data)
                                    ss.send(data_str.encode('utf-8'))
                                elif buff['type'] == Protocol.SEND_GAME_STATE.value:
                                    data = dict(type=Protocol.SEND_GAME_STATE.value,content='Game set request Recieved!')
                                    data_str = json.dumps(data)
                                    ss.send(data_str.encode('utf-8'))
                        except ConnectionAbortedError:
                            print('Connection offline:{}'.format(addr))
                            return
                except socket.timeout:
                    print("time out for connection, keep waiting for {}s".format(self.meta['closetime'] - time.time() + serve_start))
                    pass
                
        threading.Thread(target=serve_thread).start()
            
                


if __name__ == "__main__":
    server = Server('',21353)  # 服务端仅需绑定端口即可
    server.init_bind()
    client = Client('127.0.0.1',21353,5,1)  # 客户端则需要知道服务器IP以及服务端口
    server.auto_serve()
    client.init_connect()
    delay_time, rev_rate = client.measure_delay(10)
    if not isnan(delay_time):
        print('delay time: {} ms rev_rate:{:.2%}'.format(delay_time*1000,rev_rate))
    else:
        print('client error')
    client.close()




