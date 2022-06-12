import json
import socket
from enum import Enum, auto
import threading
import time
import utils

class NetType(Enum):
    Client = 0
    Server = 1

class Protocol(Enum):
    SEND_NET_STATE = auto()
    REV_NET_STATE = auto()
    SEND_MESSAGE = auto()
    SEND_MEASURE_DELAY = auto()
    RECEIVE_MEASURE_DELAY = auto()
    SEND_GAME_STATE = auto()
    RECEIVE_MESSAGE = auto()
    CLOSE_CONNECTION = auto()


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
        self.rev_lock = threading.Lock()
        self.info = dict(delay=-1,rev=0)
        
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
    
    def send_netstate(self):
        if not self.is_open:
            with self.log_lock:
                self.log_buff.append(utils.msg_with_time('Reject to send netstate, disconnected with server!'))
            return
        data = dict(type=Protocol.SEND_NET_STATE.value,content='')
        data_str = json.dumps(data)
        self.client.send(data_str.encode('utf-8'))
         
    def send_disconnection(self):
        if not self.is_open:
            with self.log_lock:
                self.log_buff.append(utils.msg_with_time('Reject to send disconnection state, disconnected with server!'))
            return
        data = dict(type=Protocol.CLOSE_CONNECTION.value,content='')
        data_str = json.dumps(data)
        self.client.send(data_str.encode('utf-8'))
        
    def send_msg(self,msg:str):
        if not self.is_open:
            with self.log_lock:
                self.log_buff.append(utils.msg_with_time('Reject to send message, disconnected with server!'))
            return
        data = dict(type=Protocol.SEND_MESSAGE.value,content=msg)
        data_str = json.dumps(data)
        try:
            self.client.send(data_str.encode('utf-8'))
        except ConnectionError:
            return
        with self.log_lock:
            self.log_buff.append(utils.msg_with_time('Message has been sent to server {}.'.format(self.meta['host'])))
        
        # 平均延迟，丢包率
    def measure_delay(self,cnt=3):
        with self.rev_lock:
            data = dict(type=Protocol.SEND_MEASURE_DELAY.value,content='request for delay')
            data_str = json.dumps(data)
            total_time = 0.0
            total_rev_packs = 0
            for _ in range(cnt):
                flag = True
                start_time = time.time()
                self.client.send(data_str.encode('utf-8'))
                try:
                    rev_data_str = self.client.recv(1024).decode('utf-8')
                except socket.timeout:
                    self.info['delay'] = -1
                    self.info['rev'] = 0
                    return -1
                except ConnectionError:
                    self.info['delay'] = -1
                    self.info['rev'] = 0
                    return -1
                while rev_data_str == '':
                    if time.time() - start_time > self.meta['max_wait_time']:
                        flag = False
                        break
                    rev_data_str = self.client.recv(1024).decode('utf-8')
                    rev_data = json.dumps(rev_data_str)
                    if isinstance(rev_data,dict) and rev_data['type'] == Protocol.RECEIVE_MEASURE_DELAY.value:
                        flag = True
                        break
                    else:
                        rev_data_str = ''
                        continue
                if flag:
                    total_time += time.time() - start_time
                    total_rev_packs += 1
            # 平均延迟，丢包率
            if total_rev_packs == 0:
                self.info['delay'] = -1
                self.info['rev'] = 0
            else:
                self.info['delay'] = total_time/total_rev_packs
                self.info['rev'] = total_rev_packs/cnt
            return 0
        
    def msg_rev_thread(self):
        while True:
            with self.open_lock:
                if not self.is_open:
                    break
            try:
                while True:
                    with self.open_lock:
                        if not self.is_open:
                            break
                    try:
                        with self.rev_lock:
                            buff_str = self.client.recv(1024).decode('utf-8')
                        if buff_str == "":  # 为空说明未收到任何数据，重新接收
                            continue
                        ## 以下为客户端的响应程序
                        buff = json.loads(buff_str)  # dict
                        if buff['type'] == Protocol.SEND_NET_STATE.value:  # 网络延迟测试    
                            data = dict(type=Protocol.REV_NET_STATE.value,content='from {}'.format(self.meta['host']))
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
                        elif buff['type'] == Protocol.CLOSE_CONNECTION.value:
                            data = dict(type=Protocol.RECEIVE_MESSAGE.value,content='Message Recieved!')
                            data_str = json.dumps(data)
                            self.client.send(data_str.encode('utf-8'))
                            with self.log_lock:
                                self.log_buff.append(utils.msg_with_time('Server broken down, try to connect again.'))
                            with self.open_lock:
                                self.is_open = False
                        elif buff['type'] == Protocol.SEND_MEASURE_DELAY.value:
                            data = dict(type=Protocol.RECEIVE_MEASURE_DELAY.value,content='Measure received')
                            data_str = json.dumps(data)
                            self.client.send(data_str.encode('utf-8'))
                        elif buff['type'] == Protocol.RECEIVE_MEASURE_DELAY.value:
                            break
                        elif buff['type'] == Protocol.REV_NET_STATE.value:
                            break
                        else:
                            data = dict(type=Protocol.SEND_NET_STATE.value,content='Unknown message received!')
                            data_str = json.dumps(data)
                            self.client.send(data_str.encode('utf-8'))
                            with self.log_lock:
                                self.log_buff.append(utils.msg_with_time('Unknown message recevied from {}'.format(self.meta['host'])))
                    except socket.timeout:
                        buff_str = ""
                        self.send_netstate()
                    except json.decoder.JSONDecodeError:
                        buff_str = ""
                    except OSError:
                        pass
                    
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
        self.rev_lock = threading.Lock()
        self.ss = None
        self.ss_ip = None
        self.info = dict(delay=-1,rev=0)
        
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
    
    def send_disconnection(self):
        with self.open_lock:
            is_open = self.is_open
        if not is_open or self.ss is None:
            with self.log_lock:
                self.log_buff.append(utils.msg_with_time('Reject to send disconnection state, none of connected client'))
        else:
            data = dict(type=Protocol.CLOSE_CONNECTION.value,content='')
            data_str = json.dumps(data)
            self.ss.send(data_str.encode('utf-8'))
    
    def measure_delay(self,cnt=3):
        if self.ss is None:
            with self.log_lock:
                self.log_buff.append(utils.msg_with_time('Reject to send message, none of connected client!'))
            return -1
        with self.rev_lock:
            data = dict(type=Protocol.SEND_MEASURE_DELAY.value,content='request for delay')
            data_str = json.dumps(data)
            total_time = 0.0
            total_rev_packs = 0
            for _ in range(cnt):
                flag = True
                start_time = time.time()
                self.ss.send(data_str.encode('utf-8'))
                try:
                    rev_data_str = self.ss.recv(1024).decode('utf-8')
                except socket.timeout:
                    self.info['delay'] = -1
                    self.info['rev'] = 0
                    return -1
                except ConnectionError:
                    self.info['delay'] = -1
                    self.info['rev'] = 0
                    return -1
                while rev_data_str == '':
                    if time.time() - start_time > self.meta['max_wait_time']:
                        flag = False
                        break
                    rev_data_str = self.ss.recv(1024).decode('utf-8')
                    rev_data = json.dumps(rev_data_str)
                    if isinstance(rev_data,dict) and rev_data['type'] == Protocol.RECEIVE_MEASURE_DELAY.value:
                        flag = True
                        break
                    else:
                        rev_data_str = ''
                        continue
                if flag:
                    total_time += time.time() - start_time
                    total_rev_packs += 1
            # 平均延迟，丢包率
            if total_rev_packs == 0:
                self.info['delay'] = -1
                self.info['rev'] = 0
            else:
                self.info['delay'] = total_time/total_rev_packs
                self.info['rev'] = total_rev_packs/cnt
            return 0
    
    def send_msg(self,msg:str):
        if self.ss is None:
            with self.log_lock:
                self.log_buff.append(utils.msg_with_time('Reject to send message, none of connected client!'))
        else:
            data = dict(type=Protocol.SEND_MESSAGE.value,content=msg)
            data_str = json.dumps(data)
            try:
                self.ss.send(data_str.encode('utf-8'))
            except ConnectionError:
                return
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
                serve_start = time.time()
                self.ss_ip = addr[0]
                with self.log_lock:
                    self.log_buff.append(utils.msg_with_time('Connection from: {}'.format(addr[0])))
                flag = True
                while flag:
                    try:
                        while flag:
                            with self.open_lock:
                                if not self.is_open:
                                    flag = False
                                    break
                            try:
                                with self.rev_lock:
                                    buff_str = self.ss.recv(1024).decode('utf-8')
                                if buff_str == "":  # 为空说明未收到任何数据，重新接收
                                    continue
                                ## 以下为服务端的响应程序
                                buff = json.loads(buff_str)  # dict
                                if buff['type'] == Protocol.SEND_NET_STATE.value:  # 网络延迟测试    
                                    data = dict(type=Protocol.REV_NET_STATE.value,content='from {}'.format(addr))
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
                                elif buff['type'] == Protocol.CLOSE_CONNECTION.value:
                                    data = dict(type=Protocol.RECEIVE_MESSAGE.value,content='Message Recieved!')
                                    data_str = json.dumps(data)
                                    self.ss.send(data_str.encode('utf-8'))
                                    with self.log_lock:
                                        self.log_buff.append(utils.msg_with_time('Client Disconnection Actively'))
                                    flag = False
                                    break
                                elif buff['type'] == Protocol.SEND_MEASURE_DELAY.value:
                                    data = dict(type=Protocol.RECEIVE_MEASURE_DELAY.value,content='Measure received')
                                    data_str = json.dumps(data)
                                    self.ss.send(data_str.encode('utf-8'))
                                elif buff['type'] == Protocol.RECEIVE_MEASURE_DELAY.value:
                                    break
                                elif buff['type'] == Protocol.REV_NET_STATE.value:
                                    break
                                else:
                                    data = dict(type=Protocol.SEND_NET_STATE.value,content='Unknown message received!')
                                    data_str = json.dumps(data)
                                    self.ss.send(data_str.encode('utf-8'))
                                    with self.log_lock:
                                        self.log_buff.append(utils.msg_with_time('Unknown message recevied from {}'.format(addr[0])))
                            except ConnectionError:
                                flag = False
                                with self.log_lock:
                                    self.log_buff.append(utils.msg_with_time('Connection Error'))
                                break
                            except json.decoder.JSONDecodeError:
                                buff_str = ""
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
            except OSError:
                with self.open_lock:
                    self.is_open = False
                self.ss = None
                self.ss_ip = None
                break
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
            
        
                   





