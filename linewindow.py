from functools import wraps

def drawing(func):
    @wraps(func)
    def new_func(self, *args, **kwargs):
        val = func(self, *args, **kwargs)
        self.padmanager.drawstr(self.vwin.start, 65, str(self.fwin))
        self.padmanager.drawstr(self.vwin.start, 80, str(self.vwin))
    return new_func


class LineWindowManager(object):
    def __init__(self, flen, floader, bpl, buffers, padmanager, viewH):

        self.flen = flen
        self.full_win = _Window(0, flen+1)
        # Reasoning for + 1: file_end is a non-inclusive bound,
        #   in order for the last line to be loaded it has to
        #   be before file_end

        self.floader = floader
        self.bpl = bpl
        self.buffers = buffers
        self.padmanager = padmanager
        self.viewH = viewH

        self.fwin = _Window(0,0)
        self.vwin = _Window(0,self.viewH)

    def move_fwindow(self, start):
        margin = self.viewH
        file_start = start - margin
        file_end = start + self.viewH + margin
        fwin = _Window(file_start, file_end)

        self.fwin = self.full_win.compress(fwin)

        byte_win = self.fwin * self.bpl

        self.floader(byte_win.start, byte_win.end)

    def incr_vwindow(self):
        new_win = self.vwin + 1

        if new_win.end <= self.buffers.screenend():
            self.padmanager.set_line(new_win.start)
            self.vwin = new_win
            return

        if self.fwin.end >= self.flen + 1:
            # File window can't increase past end of file
            return

        last_line = self.fwin.end

        current_line = self.buffers.screenToLine(self.vwin.start) + self.fwin.start

        self.move_fwindow(current_line)

        last_screen = self.buffers.lineToScreen(last_line - self.fwin.start)
        start_screen = last_screen - self.viewH + 1

        self.padmanager.set_line(start_screen)
        self.vwin = _Window(start_screen, start_screen + self.viewH)

    def decr_vwindow(self):
        new_win = self.vwin - 1

        if new_win.start >= 0:
            self.padmanager.set_line(new_win.start)
            self.vwin = new_win
            return

        if self.fwin.start <= 0:
            # File window can't decrease before start of file
            return

        current_line = self.fwin.start

        self.move_fwindow(current_line)

        start_screen = self.buffers.lineToScreen(current_line - self.fwin.start)
        self.padmanager.set_line(start_screen - 1)
        self.vwin = _Window(start_screen - 1, start_screen + self.viewH - 1)

    # This will jump the view window directly to the given
    #   file line. Note that this cannot end up at a
    #   particular screen line like change_vwindow can.
    def move_vwindow(self, line):
        line_win = _Window(line, line + self.viewH)

        if not self.fwin.contains(line_win):
            self.change_fwindow(line)

        start_screen = self.buffers.lineToScreen(line)
        new_win = _Window(start_screen, start_screen + self.viewH)
        if new_win.end > self.flen + 1:
            offset = self.flen + 1 - new_win.end
            new_win += offset

        self.change_vwindow(new_win.start)
        self.vwin = new_win


class _Window(object):
    def __init__(self, start, end):
        if start > end:
            raise ValueError("Window ends before it starts- %s:%s" % (str(start), str(end)))

        self.start = start
        self.end = end

    def contains(self, win):
        return win.start >= self.start and win.end <= self.end

    def compress(self, win):
        x = win.start
        y = win.end
        if x < self.start:
            x = self.start
        if y > self.end:
            y = self.end

        return _Window(x,y)

    def shift_into(self, win):
        if win.start < self.start:
            win = win + (self.start - win.start)
        elif win.end > self.end:
            win = win + (win.end - self.end)
        return self.compress(win)

    def apply(self, func):
        x = func(self.start)
        y = func(self.end)
        return _Window(x,y)

    def __add__(self, val):
        return _Window(self.start + val, self.end + val)

    def __sub__(self, val):
        return self.__add__(-1 * val)

    def __mul__(self, val):
        return _Window(self.start * val, self.end * val)

    def __radd__(self, val):
        return self.__add__(val)

    def __rsub__(self, val):
        return (-1 * self) + val

    def __rmul__(self, val):
        return self.__mul__(val)

    def __iadd__(self, val):
        self.start += val
        self.end += val
        return self

    def __isub__(self, val):
        return self.__iadd__(-1*val)

    def __imul__(self, val):
        self.start *= val
        self.end *= val
        return self

    def __gt__(self, win):
        return self.end > win.end

    def __lt__(self, win):
        return self.start < win.start

    def __str__(self):
        return "[%i -> %i]" % (self.start, self.end)

