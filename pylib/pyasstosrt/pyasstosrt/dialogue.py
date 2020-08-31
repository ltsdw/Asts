from .time import Time

class Dialogue(object):
    def __init__(self, index, start, end, text):
        self.index = index
        self.start = Time(start)
        self.end = Time(end)
        self.text = text

    def getTimestamp(self):
        return f"{self.start} --> {self.end}"

    def __str__(self):
        return f"{self.index}\n{self.getTimestamp()}\n{self.text}\n\n"

