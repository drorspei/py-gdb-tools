import sys


class mytracer(object):
    def __init__(self):
        self.breakpoints = []
        self.break_stack = []
        self.log = []

    def tracecall(self, frame, event, arg):
        if event == 'call':
            breaks = [(doline, varname, logtup)
                      for docallbreak, doline, varname, logtup in self.breakpoints
                      if docallbreak(frame)]
            if breaks:
                self.break_stack.append(breaks)
                return self.traceline

    def traceline(self, frame, event, arg):
        for doline, evalfunc, logtup in self.break_stack[-1]:
            if doline(frame, event):
                try:
                    value = evalfunc(frame, arg)
                except Exception as e:
                    value = e
                self.log.append((logtup, value))

        if event == 'return':
            self.break_stack.pop()

        return self.traceline

    def __enter__(self):
        sys.settrace(self.tracecall)

    def __exit__(self, *args, **kwargs):
        sys.settrace(None)

    def dump_at_file_line(self, filename, lineno, varname):
        def docallbreak(frame):
            return filename in frame.f_code.co_filename

        def doline(frame, event):
            return frame.f_lineno == lineno and event == 'line'

        evalfunc = self._stdevalfunc(varname)

        self.breakpoints.append((docallbreak, doline, evalfunc, (filename, lineno, varname)))

    def dump_at_func_line(self, func, lineno, varname):
        func_name = func.__name__
        func_line = func.func_code.co_firstlineno + lineno
        filename = func.func_code.co_filename

        def docallbreak(frame):
            return (filename in frame.f_code.co_filename
                    and (frame.f_code.co_name == func_name  # Actually same function.
                         or func.func_code.co_firstlineno < frame.f_lineno < func_line))  # Function defined inside.

        def doline(frame, event):
            return frame.f_lineno == func_line and event == 'line'

        evalfunc = self._stdevalfunc(varname)

        self.breakpoints.append((docallbreak, doline, evalfunc,
                                 (func.func_code.co_filename, func_name, lineno, varname)))

    def dump_at_func_return(self, func, varname='__return__'):
        func_name = func.__name__
        filename = func.func_code.co_filename

        def docallbreak(frame):
            return filename in frame.f_code.co_filename and frame.f_code.co_name == func_name

        def doline(frame, event):
            return event == 'return'

        if varname == '__return__':
            def evalfunc(frame, arg):
                return arg
        else:
            evalfunc = self._stdevalfunc(varname)

        self.breakpoints.append((docallbreak, doline, evalfunc,
                                 (func.func_code.co_filename, func_name, 'return')))

    @staticmethod
    def _stdevalfunc(varname):
        def evalfunc(frame, arg):
            lcls = dict(frame.f_locals)
            lcls['__frame__'] = frame
            return eval(varname, frame.f_globals, lcls)
        return evalfunc


if __name__ == "__main__":
    def foo():
        z = 10
        def goo():
            x = 11
            y = x * 2
            x = y + 1
            return 2
        return goo() + z

    mt = mytracer()
    mt.dump_at_func_line(foo, 5, "y")  # , __frame__.f_back.f_locals['z']
    # mt.atfuncreturn(foo)

    with mt:
        foo()

    print mt.log