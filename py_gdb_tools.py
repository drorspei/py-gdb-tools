def define_commands():
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
                sym = arg[0]
            
            send_double_vec(sym, port)

    SendDoubleVectorCommand()


try:
    import gdb
except ImportError:
    pass
else:
    define_commands()


def get_std_vector_buff(name):
    val = gdb.parse_and_eval(name)
    if str(val.type).startswith('std::vector<double,'):
        addr = gdb.parse_and_eval('*{}._M_impl._M_start'.format(name)).address
        length = int(gdb.parse_and_eval('{0}._M_impl._M_finish - {0}._M_impl._M_start'.format(name)))
        sizeof = int(gdb.parse_and_eval('sizeof(*{}._M_impl._M_start)'.format(name)))
        buff = gdb.selected_inferior().read_memory(addr, length * sizeof)

        return buff, length, sizeof


def get_eigen_matrix_buff(name):
    val = gdb.parse_and_eval(name)
    typ = str(val.type)
    if typ.startswith('Eigen::Matrix<double,') or typ.startswith('Eigen::VectorXd'):
        addr = gdb.parse_and_eval('*{}.data()'.format(name)).address
        length = int(gdb.parse_and_eval('{0}.size()'.format(name)))
        sizeof = int(gdb.parse_and_eval('sizeof(*{}.data())'.format(name)))
        buff = gdb.selected_inferior().read_memory(addr, length * sizeof)

        return buff, length, sizeof


def send_double_vec(name, port=50010):
    import socket
    import gdb

    print('got:', name)

    for get_type_func in [get_std_vector_buff, get_eigen_matrix_buff]:
        res = get_type_func(name)
        if res is not None:
            buff, length, sizeof = res
            break
    else:
        raise TypeError("Type isn't std::vector<double> or Eigen::Matrix<double>")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', port))

    try:
        s.sendall(('%016d' % length).encode())
        s.sendall(buff[:length * sizeof])
    finally:
        s.close()
