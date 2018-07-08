# py-gdb-tools
Tools for interacting with gdb from another python process

There's currently a single thing this project can do: send a vector of doubles from gdb to a python shell. Here's how it works:

1. Run gdb with some process,
2. enter in `source /path/to/py_gdb_tools_server.py`,
3. in python load `py_gdb_tools_server.py` (say with `execfile` or `exec`),
4. enter `vec = recv_double_vec()` in python,
5. enter `send_double_vec symbol_name`,
6. you should now have a variable called `vec` in python!

Sending a vector from gdb to python is helpful in case you want to plot the vector, do some analysis in the middle of debugging, or compare with other values.

If you're having trouble with the default port of 50010, use `send_double_vec port=PORT symbol_name` in gdb and `vec = recv_double_vec(port=PORT)` in python.