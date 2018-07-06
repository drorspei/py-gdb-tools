def recv_double_array(PORT=50010):
    import socket
    import numpy as np
    
    HOST = 'localhost'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((HOST, PORT))
        s.listen(1)
        conn, addr = s.accept()
        try:
            data = ''
            while 1:
                ndata = conn.recv(1024 * 16)
                if not ndata: break
                data += ndata
            conn.close()
            s.close()
            return np.array(list(map(int, data.split(', '))), np.uint64).view(np.float64)
        finally:
            conn.close()
    finally:
        s.close()


def send_double_ptr(ptrname, length, port=50010, chunk=999):
    import socket
    import gdb
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', port))
    pos = 0
    while pos < length - chunk:
        s.sendall(str(gdb.parse_and_eval("*(uint64_t*)(void*)({} + {})@{}".format(ptrname, pos, chunk)))[1:-1].encode())
        pos += chunk
        if pos < length:
            s.sendall(', '.encode())
    if pos < length:
        s.sendall(str(gdb.parse_and_eval("*(uint64_t*)(void*)({} + {})@{}".format(ptrname, pos, length - pos)))[1:-1].encode())
    s.close()