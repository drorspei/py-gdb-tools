# py-gdb-tools
A library for extracting values from gdb - in a separate python process.

Currently you can only extract `std::vector<double>` or `Eigen::Matrix<double>`, or the same classes with `double` replaced by `std::complex<double>`. Later editions will add support for all primitives and combinations of stl classes and primitives. It's just that I personally need to debug vectors of doubles a lot...

Extracting can mean one of two things: either sending the value over to a running python process, or saving to a file that can be read later with python. The first option is useful for dynamic debugging - get to a breakpoint, send the value over to python, analyze it a bit, say, with a plot, then find your bug. The second option is useful for letting the program run for a while, saving values to a file as it goes, then reading that file and looking at everything somehow, say, with a big plot. Sometime soon I'll write a similar feature for pdb ("python's gdb"), and then you could automatically compare values from a c++ process with values from a python process.

In the rest of this readme I explain how to send values over to python, how to save to and read from a file, how to save automatically without stopping at the breakpoints, and how to send automatically to a running python process. There are also explanations of how to send single values with old syntax that I was using as I was writing this library, with a nifty screen cast gif, though these are less relevant now.

The automatic file saving approach allows you to gather logs of a run without instrumenting your program. The main trade-off here is between the performance hit of running under gdb, and the time it would take to write logging into your code. For certain application, such as comparing c++ code with python code (which I do often), the performance of the run is not an issue, while adding logging is quite the hassle. py-gdb-tools offers a quick solution for big debugging jobs.

## Getting vector/Eigen::Matrix values from gdb in python:

Running `py_gdb_tools_gdb.py` (with `source`) starts a server in the background that listens to requests for values of vectors/Eigen matrices. Here's how to use it:

1. Run gdb on your process,
2. enter `source /path/tp/py_gdb_tools_gdb.py`,
3. set a breakpoint somewhere,
4. run the process and reach the breakpoint,
5. run python and import/execfile `py_gdb_tools_python.py`,
6. enter in python:

```
pgt = PgtPythonSide().start()
val = pgt.get('symbol_name')
```

7. that's it, you have a numpy array in `val`.

## Saving values to a file:

py-gdb-tools adds the command `pgt_var_to_file` to your gdb which lets you save a variable to a file and later read it from python using `read_pgt_file`:

1. Run gdb and source `py_gdb_tools_gdb.py`,
2. enter `pgt_var_to_file path/to/file.cpp:lineno symbol_name /path/to/output/file`,
3. run program,
4. in python use `read_pgt_file('/path/to/output/file')`

Note that `read_pgt_file` is a generator that yields pairs of variable names and associated data.

## Automating saving values to a file:

It's also easy to create a script that will add breakpoints that save variables to a file. For example, say we want to debug `example.cpp` from the examples folder. We create a file `example.py` that contains the line

    VarToFileBreakpoint('examples/example.cpp:6', 'v', '/tmp/example.pgt')

Now we can run gdb, source `py_gdb_tools_gdb.py`, then source `examples/example.py`, and finally let gdb run. The program will run and exit normally, and we'll have a new file at `/tmp/example.pgt`. We can read the file using `read_pgt_file` from `py_gdb_tools_python.py`.

## Automating sending values to a server:

Similarly to saving to a file, you can use `VarToServerBreakpoint` in a python script to automate sending values to a listening server.

## Automatically loading py-gdb-tools in all of your gdb session:

On linux (or at least on my ubuntu) there's a file that gdb runs every time, and it is located at `/etc/gdb/gdbinit` (on some machines I've worked on it was at `/etc/gdb/.gdbinit`). You can add the following line to the file, and py-gdb-tools will be loaded automatically in all of your gdb sessions:

    source /path/to/py_gdb_tools_gdb.py

## Sending a single vector/Eigen::Matrix from gdb to python:

This was written before the gdb-side server option and might still be relevant in some cases.

1. Run gdb with some process,
2. enter in `source /path/to/py_gdb_tools_gdb.py`,
3. in python load `py_gdb_tools_python.py` (say with `execfile` or `exec`),
4. enter `vec = recv_double_vec()` in python,
5. enter `send_double_vec symbol_name` in gdb,
6. you should now have a variable called `vec` in python!

Sending a vector from gdb to python is helpful in case you want to plot the vector, do some analysis in the middle of debugging, or compare with other values.

To use a different port than the default of 50010, use `send_double_vec port=PORT symbol_name` in gdb and `vec = recv_double_vec(port=PORT)` in python.

![Image](https://github.com/drorspei/py-gdb-tools/blob/master/examples/example.gif)

## Sending many vectors/eigen matrices:

The following was also written before the gdb-side server option, so maybe not so relevant anymore.

If you're going to be sending many values, you can use the `PgtPythonSide` class on the python side. It listens in the background for incoming data, so you don't need to write `recv_double_vec` yourself:

1. Run gdb with some process,
2. enter in `source /path/to/py_gdb_tools_gdb.py`,
3. in python load `py_gdb_tools_python.py` (say with `execfile` or `exec`),
4. enter `pgt = PgtPythonSide().start()` in python,
5. enter `send_double_vec symbol_name`,
6. you can now access the variable using `pgt.received[-1]` or `pgt.vars['symbol_name']`

### Requirements

Um this is a bit awkward... Currently `py_gdb_tools_gdb.py` is written for python 3, and `py_gdb_tools_python.py` is written for python 2.7. This is because my gdb runs python 3, but I use python 2.7 at my work. This can easily be dealt with if the need arises.