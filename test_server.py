from network import Server

if __name__ == "__main__":
    server = Server('',9820)  # 服务端仅需绑定端口即可
    server.init_bind()
    server.auto_serve()