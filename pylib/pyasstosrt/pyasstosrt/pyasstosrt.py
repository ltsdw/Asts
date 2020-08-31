import os
import re
from pathlib import Path
from .dialogue import Dialogue


class Subtitle(object):
    def __init__(self, filepath):
        self.filepath   = filepath
        self.file       = Path(filepath).stem
        self.raw_text   = self.getText()
        self.dialogues  = list()

    def getText(self):
        return Path(self.filepath).read_text(encoding="utf8")

    def convert(self):
        cleaning_old_format = re.compile(r"{.*?}")
        dialog_mask         = re.compile(r"Dialogue: \d+?,(\d:\d{2}:\d{2}.\d{2}),(\d:\d{2}:\d{2}.\d{2}),.*?,\d+,\d+,\d+,.*?,(.*)")
        dialogs             = re.findall(dialog_mask, re.sub(cleaning_old_format, "", self.raw_text))
        dialogs             = sorted(list(filter(lambda x: x[2], dialogs)))

        self.subtitleFormatting(dialogs)

    @staticmethod
    def textClearing(raw_text: str):
        text        = raw_text.replace('\h', '\xa0').strip()
        line_text   = text.split(r'\N')

        return '\n'.join([item.strip() for item in line_text]).strip()

    def subtitleFormatting(self, dialogues):
        for index, values in enumerate(dialogues, start=1):
            start, end, text = values
            text = self.textClearing(text.strip())
            dialogue = Dialogue(index, start, end, text)
            self.dialogues.append(dialogue)

    def export(self, output_dir=None):
        self.convert()

        path = Path(self.filepath)

        return self.dialogues

