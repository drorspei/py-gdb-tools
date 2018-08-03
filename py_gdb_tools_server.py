import socket
import threading
import collections
import numpy as np


SERIALIZE_VERSION = '1.0'
# ('%10s%100s%016d' % (SERIALIZE_VERSION, name, length * (sizeof // 8))).encode() + buff[:length * sizeof]
STOP_SOCKET = 'stopsocket'

def read_double_vec_1_0(readfunc, verbose=True):
    name = readfunc(100).strip()
    length = int(readfunc(16))

    if verbose:
        print 'reading: %s, of length %d' % (name, length)

    arr = np.empty(length, np.float64)
    buff = arr.data
    total_bytes = 8 * length
    received_bytes = 0
    while received_bytes < total_bytes:
        data = readfunc(min(1024 * 16, total_bytes - received_bytes))
        if not data:
            raise IOError("not enough data, file/socket is corrupt.")
        buff[received_bytes:received_bytes + len(data)] = data
        received_bytes += len(data)

    return name, arr


def read_by_version(readfunc):
    version = readfunc(10)
    if version == '%10s' % '1.0':
        return read_double_vec_1_0(readfunc)
    elif version == '':
        raise StopIteration("didn't receive more data.")
    else:
        raise IOError('serialize version is corrupt.')


def recv_named_double_vec(port=50010):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('localhost', port))
        s.listen(1)
        conn, _ = s.accept()
        try:
            return read_by_version(conn.recv)
        finally:
            conn.close()
    finally:
        s.close()


def recv_double_vec(port=50010):
    return recv_named_double_vec(port)[1]


def read_pgt_file(filepath):
    with open(filepath, 'rb') as f:
        while True:
            try:
                yield read_by_version(f.read)
            except StopIteration:
                break


class PgtServer(object):
    """
    Server to receive vectors from gdb in background

    Start the server by calling `start`, and access incoming data using either
    `received` or `vars`:
        `received` - a list of pairs, name and data, of all received vectors from gdb.

        `vars` - an ordered dictionary of names to most recent sent data.
    """
    def __init__(self, port=50010):
        self.port = port
        self.received = []
        self.vars = collections.OrderedDict()

    def start(self):
        thread = threading.Thread(target=self._run)
        thread.daemon = True
        thread.start()
        return self

    def _run(self):
        while True:
            try:
                name, arr = recv_named_double_vec(self.port)
                self.received.append((name, arr))
                self.vars[name] = arr
            except StopIteration:
                print "done running :)"
                break

    def stop(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', self.port))
        s.close()
