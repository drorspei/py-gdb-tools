import atexit
import socket

SERIALIZE_VERSION = '2.0'

_server_port = None
_server_dones = {}


def gdbprintln(text):
    def inner():
        gdb.write('\n(pgt) ' + text + '\n(gdb) ')
    gdb.post_event(inner)


def consume_socket(s):
    while s.recv(1024):
        pass

def stop_server(port):
    gdbprintln('exiting')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('localhost', port))
        s.sendall(('%100s' % 'stopgdbservernowplease').encode())
        _server_dones[port].wait(1)
    except ConnectionRefusedError:
        pass
    else:
        consume_socket(s)
        s.shutdown(socket.SHUT_RDWR)
    finally:
        s.close()


def start_server(port=50018):
    def inner(done_event):
        global _server_port
        if _server_port is not None:
            gdbprintln("server already running on port %r" % _server_port)
            return

        done.wait(0.5)

        _server_port = port
        import socket
        import gdb

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('localhost', port))
        except OSError:
            gdbprintln("server couldn't start since port is already in use")
            return
        
        gdbprintln('server start on port %r' % port)
        try:
            while True:
                s.listen(1)
                conn, _ = s.accept()
                try:
                    buff = conn.recv(116).decode()
                    pyport = int(buff[:16])
                    name = buff[16:].strip()
                except Exception as e:
                    consume_socket(conn)
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()
                    raise e
                if name == 'stopgdbservernowplease':
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()
                    done_event.set()
                    break
                def defer_send():
                    send_double_vec(name, pyport)
                gdb.post_event(defer_send)
        finally:
            _server_port = None
            s.shutdown(socket.SHUT_RDWR)
            s.close()

    
    import threading
    done = threading.Event()

    _server_dones[port] = done
    atexit.register(stop_server, port)
    thread = threading.Thread(target=inner, args=(done,), daemon=True)
    thread.daemon = True
    thread.start()



try:
    import gdb
except ImportError:
    pass
else:
    class SendDoubleVectorCommand (gdb.Command):
        """Sends a double vector to a socket"""

        def __init__ (self):
            super (SendDoubleVectorCommand, self).__init__("send_double_vec", 
                                                           gdb.COMMAND_SUPPORT, 
                                                           gdb.COMPLETE_SYMBOL)

        def invoke (self, arg, from_tty):
            args = arg.split()
            if args[0].startswith('port='):
                port = int(args[0][5:])
                sym = args[1]
            else:
                port = 50010
                sym = args[0]
            
            send_double_vec(sym, port)

    SendDoubleVectorCommand()

    class VarToFileBreakpoint(gdb.Breakpoint):
        def __init__(self, breakpoint, varname, output_file, stop_execution=False, verbose=False, num_up=0):
            """
            Save (really append) variable to file at breakpoint

            @param breakpoint: Where to put the breakpoint. Use this format: "/path/to/file.cpp:lineno".
            @type breakpoint: str
            @param varname: Expression for variable.
            @type varname: str
            @param output_file: Path to output file.
            @type output_file: str
            @param stop_execution: If True execution will stop at breakpoint and wait for user input.
            @type stop_execution: bool
            """
            super().__init__(breakpoint)
            self.varname = varname
            self.output_file = output_file
            self.stop_execution = stop_execution
            self.verbose = verbose
            self.num_up = num_up

        def stop(self):
            if self.verbose:
                gdbprintln('saving to file: %s' % self.varname)
            
            if self.num_up:
                gdb.execute("up-silently {}".format(self.num_up))

            try:
                with open(self.output_file, 'ab') as f:
                    f.write(double_vec_to_buffer(self.varname))
                return self.stop_execution
            finally:
                if self.num_up:
                    gdb.execute("down-silently {}".format(self.num_up))


    class VarToServerBreakpoint(gdb.Breakpoint):
        def __init__(self, breakpoint, varname, port=50010, stop_execution=False, verbose=False):
            """
            Send variable to listening python.

            @param breakpoint: Where to put the breakpoint. Use this format: "/path/to/file.cpp:lineno".
            @type breakpoint: str
            @param varname: Expression for variable.
            @type varname: str
            @param port: Port to send to.
            @type port: int
            @param stop_execution: If True execution will stop at breakpoint and wait for user input.
            @type stop_execution: bool
            """
            super().__init__(breakpoint)
            self.varname = varname
            self.port = port
            self.stop_execution = stop_execution
            self.verbose = verbose

        def stop(self):
            if self.verbose:
                gdbprintln('sending to socket: %s' % self.varname)
            send_double_vec(self.varname, port=self.port)
            return self.stop_execution

    class VarToFile(gdb.Command):
        """Appends variable to file"""
        def __init__(self):
            super().__init__("pgt_var_to_file", gdb.COMMAND_SUPPORT, gdb.COMPLETE_SYMBOL)

        def invoke(self, arg, from_tty):
            try:
                break_loc, varname, output_file = arg.split()
            except ValueError:
                gdbprintln('usage (no more spaces allowed!): pgt_var_to_file break_location varname output')
                return
            else:
                VarToFileBreakpoint(break_loc, varname, output_file)

    VarToFile()

    start_server()


def serialize_error_message(name, message):
    return ('%10s%100s%04d%016d%s' % (SERIALIZE_VERSION, name, 0, -len(message), message)).encode()


def get_std_vector_buff(name):
    try:
        val = gdb.parse_and_eval(name)
    except:
        return serialize_error_message(name, "Gdb couldn't parse name")

    str_type = str(val.type)
    if str_type.startswith('const '):
        str_type = str_type[len('const '):]

    if str_type.startswith('std::vector<double,'):
        addr = gdb.parse_and_eval('*{}._M_impl._M_start'.format(name)).address
        length = int(gdb.parse_and_eval('{0}._M_impl._M_finish - {0}._M_impl._M_start'.format(name)))
        sizeof = int(gdb.parse_and_eval('sizeof(*{}._M_impl._M_start)'.format(name)))
        buff = gdb.selected_inferior().read_memory(addr, length * sizeof)

        return ('%10s%100s%04d%016d' % (SERIALIZE_VERSION, name, 0, length * (sizeof // 8))).encode() + buff[:length * sizeof]


def get_eigen_matrix_buff(name):
    val = gdb.parse_and_eval(name)
    str_type = str(val.type)
    if str_type.startswith('const '):
        str_type = str_type[len('const '):]

    starts = ['Eigen::Matrix', 'Eigen::VectorXd', 'Eigen::VectorXcd']

    if any(str_type.startswith(start) for start in starts):
        addr = gdb.parse_and_eval('*{}.data()'.format(name)).address
        length = int(gdb.parse_and_eval('{0}.size()'.format(name)))
        sizeof = int(gdb.parse_and_eval('sizeof(*{}.data())'.format(name)))
        buff = gdb.selected_inferior().read_memory(addr, length * sizeof)

        return ('%10s%100s%04d%016d' % (SERIALIZE_VERSION, name, 0, length * (sizeof // 8))).encode() + buff[:length * sizeof]


def get_single_integer(name):
    val = gdb.parse_and_eval(name)
    str_type = str(val.type)
    if str_type.startswith('const '):
        str_type = str_type[len('const '):]

    starts = ['size_t', 'std::size_t', 'unsigned long', 'int', 'unsigned int']

    if any(str_type.startswith(start) for start in starts):
        return ('%10s%100s%04d%025d' % (SERIALIZE_VERSION, name, 1, int(val))).encode()


def double_vec_to_buffer(name):
    import gdb

    assert len(name) < 100, "variable name must be less than 100 characters"

    for get_type_func in [get_std_vector_buff, get_eigen_matrix_buff, get_single_integer]:
        res = get_type_func(name)
        if res is not None:
            return res
    else:
        message = "Type '%r' wasn't recognised." % str(gdb.parse_and_eval(name).type)
        return serialize_error_message(name, message)


def send_double_vec(name, port=50077):
    buff = double_vec_to_buffer(name)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', port))

    try:
        s.sendall(buff)
    finally:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
