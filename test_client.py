from network import Client


if __name__ == "__main__":
    client = Client('10.106.25.181',9820,5,1)  # 客户端则需要知道服务器IP以及服务端口
    client.init_connect()
    client.mesaure_msg(10)
    client.close()