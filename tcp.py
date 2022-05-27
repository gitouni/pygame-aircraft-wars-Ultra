#! /usr/bin/python2
# coding=utf-8
from ast import expr_context
import json
import socket
from enum import Enum
import threading
import time
from math import isnan

class Client_Protocol(Enum):
    SEND_NET_STATE = 0
    SEND_MESSAGE = 1
    SEND_GAME_STATE = 2


class Client:
    def __init__(self,host:str,port:int,timeout:float=5.0,max_wait_time:float=1.0):
        self.meta = dict(host=host,port=port,timeout=timeout,max_wait_time=max_wait_time)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_open = False
    def init_connect(self)->bool:
        if self.is_open:
            return True
        try:
            self.client.settimeout(self.meta['timeout'])
            self.client.connect((self.meta['host'],self.meta['port']))
            self.is_open = True
            return True
        except socket.timeout:
            return False
    def close(self):
        self.client.close()
        self.is_open = False
    def sendmsg(self,msg:str):
        data = dict(type=Client_Protocol.SEND_MESSAGE.value,content=msg)
        data_str = json.dumps(data)
        self.client.sendall(data_str)
    def messaure_delay(self,cnt=10):
        data = dict(type=Client_Protocol.SEND_NET_STATE.value,content='request for delay')
        data_str = json.dumps(data)
        total_time = 0.0
        total_rev_packs = 0
        for _ in range(cnt):
            flag = True
            start_time = time.time()
            self.client.sendall(data_str.encode('utf-8'))
            try:
                rev_data_str = self.client.recv(1024)
            except socket.timeout:
                return float('nan'), 0
            while rev_data_str == '':
                self.client.recv(1024)
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
    
class Server:
    def __init__(self,host:str,port:int,timeout:float=5.0):
        self.meta = dict(host=host,port=port)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.settimeout(timeout)
        self.is_open = False
    def init_bind(self):
        self.server.bind((self.meta['host'],self.meta['port']))
        self.server.listen(5)
    def serve(self):
        def serve_thread():
            try:
                ss, addr = self.server.accept()
            except socket.timeout:
                print("time out")
                return
            while True:
                try:
                    data = dict(type=Client_Protocol.SEND_NET_STATE.value,content='from {}'.format(addr))
                    data_str = json.dumps(data)
                    ss.send(data_str.encode('utf-8'))
                    buff = ss.recv(1024).decode('utf-8')
                    print(buff)
                except ConnectionAbortedError:
                    print('Connection offline:{}'.format(addr))
                    return
        threading.Thread(target=serve_thread).start()
            
                


if __name__ == "__main__":
    server = Server('0.0.0.0',21353)
    server.init_bind()
    client = Client('127.0.0.1',21353,5,1)
    server.serve()
    client.init_connect()
    delay_time, rev_rate = client.messaure_delay(10)
    if not isnan(delay_time):
        print('delay time: {} ms rev_rate:{:.2%}'.format(delay_time*1000,rev_rate))
    else:
        print('client error')
    client.close()




