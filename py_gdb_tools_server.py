def recv_double_vec(PORT=50010):
    import socket
    import numpy as np
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('localhost', PORT))
        s.listen(1)
        conn, _ = s.accept()
        try:
            length = int(conn.recv(16))
            arr = np.empty(length, np.float64)
            buff = arr.data
            total_bytes = 8 * length
            received_bytes = 0
            while received_bytes < total_bytes:
                data = conn.recv(1024 * 16)
                if not data: break
                buff[received_bytes:received_bytes + len(data)] = data
                received_bytes += len(data)
            conn.close()
            s.close()
            return arr
        finally:
            conn.close()
    finally:
        s.close()
