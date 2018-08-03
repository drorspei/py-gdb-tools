# py-gdb-tools
Tools for interacting with gdb from another python process

## Sending a single vector/Eigen::Matrix:

1. Run gdb with some process,
2. enter in `source /path/to/py_gdb_tools.py`,
3. in python load `py_gdb_tools_server.py` (say with `execfile` or `exec`),
4. enter `vec = recv_double_vec()` in python,
5. enter `send_double_vec symbol_name` in gdb,
6. you should now have a variable called `vec` in python!

Sending a vector from gdb to python is helpful in case you want to plot the vector, do some analysis in the middle of debugging, or compare with other values.

To use a different port than the default of 50010, use `send_double_vec port=PORT symbol_name` in gdb and `vec = recv_double_vec(port=PORT)` in python.

![Image](https://github.com/drorspei/py-gdb-tools/blob/master/examples/example.gif)

## Sending many vectors/eigen matrices:

If you're going to be sending many values, you can use the `PgtServer` class on the python side. It listens in the background for incoming data, so you don't need to write `recv_double_vec` yourself:

1. Run gdb with some process,
2. enter in `source /path/to/py_gdb_tools.py`,
3. in python load `py_gdb_tools_server.py` (say with `execfile` or `exec`),
4. enter `pgt = PgtServer().start()` in python,
5. enter `send_double_vec symbol_name`,
6. you can now access the variable using `pgt.received[-1]` or `pgt.vars['symbol_name']`

## Saving values to a file:

py-gdb-tools adds the command `pgt_var_to_file` to your gdb which lets you save a variable to a file and later read it from python using `read_pgt_file`:

1. Run gdb and source `py_gdb_tools.py`,
2. enter `pgt_var_to_file path/to/file.cpp:lineno symbol_name /path/to/output/file`,
3. run program,
4. in python use `read_pgt_file('/path/to/output/file')`

Note that `read_pgt_file` is a generator that yields pairs of variable names and associated data.

## Automating saving values to a file:

It's also easy to create a script that will add breakpoints that save variables to a file. For example, say we want to debug `example.cpp` from the examples folder. We create a file `example.py` that contains the line

    VarToFileBreakpoint('examples/example.cpp:6', 'v', '/tmp/example.pgt')

Now we can run gdb, source `py_gdb_tools.py`, then source `examples/example.py`, and finally let gdb run. The program will run and exit normally, and we'll have a new file at `/tmp/example.pgt`. We can read the file using `read_pgt_file`.

## Automating sending values to a server:

Similarly to saving to a file, you can use `VarToServerBreakpoint` in a python script to automate sending values to a listening server.