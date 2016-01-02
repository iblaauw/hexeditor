import curses
from buffer import BufferStream

############## Edit Pad Config #################
class EditPadConfig(object):
    def __init__(self, bytesPerLine=8, heightcapacity=100):
        self.bytesPerLine = 8
        self.heightcapacity = 100
        self.columns = []
        self.columngaps = []
        self.columnlens = []
        self.streams = []

    def addcolumn(self, gap):
        self.columngaps.append(gap)

    def addstream(self, instream, outstream, column):
        self.streams.append((instream, outstream, column))

    def computecolumns(self):
        assert(len(self.columnlens) == len(self.columngaps))
        offset = 0
        for l,g in zip(self.columnlens, self.columngaps):
            val = (offset, offset+l)
            self.columns.append(val)
            offset += l + g

    def __len__(self):
        return len(self.columngaps)


def CreateDefaultConfig():
    config = EditPadConfig()

    config.addcolumn(3)
    config.addcolumn(4)
    config.addcolumn(4)

    st1 = BufferStream(IndexToLineNum)
    st2 = BufferStream(BytesToByteLine)
    st3 = BufferStream(BytesToNormalStr)

    config.addstream(st1, st1, 0)
    config.addstream(st2, st2, 1)
    config.addstream(st3, st3, 2)

    return config

####### Stream Functions ########
def BytesToByteLine(token):
    byteList = memoryview(token).tolist()
    byteStrs = map(_bytesToHex, byteList)
    return ' '.join(byteStrs)

def BytesToNormalStr(token):
    byteList = memoryview(token).tolist()
    byteStrs = map(curses.unctrl, byteList)
    padded = map(_padTo3, byteStrs)
    return ''.join(padded)

# Helper for BytesToByteLine
def _bytesToHex(val):
    if val > 255 or val < 0:
        return "XX"

    val = hex(val)[2:] # Chop of the inital '0x'
    val = val.upper()
    if len(val) == 1:
        val = '0' + val

    return val

# Helper for BytesToNormalStr
def _padTo3(word):
    while len(word) < 3:
        word += ' '
    return word

def IndexToLineNum(val):
    return hex(val).upper()


