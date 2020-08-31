class Time(object):

    def __init__(self, text):
        s = text.split(':')
        self.hour, self.minute = [int(sr) for sr in s[:-1]]
        self.second, self.millisecond = [int(sr) for sr in s[-1].split('.')]
        # fix for srt
        self.millisecond *= 10

    def __sub__(self, other):
        return (self.hour - other.hour) * 3600 + \
               (self.minute - other.minute) * 60 + \
               (self.second - other.second) + \
               (self.millisecond - other.millisecond) / 1000

    def __str__(self):
        return f'{self.hour:02d}:{self.minute:02d}:{self.second:02d},{self.millisecond:03d}'
