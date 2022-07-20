class TypeAliases:
    def __init__(self):
        from typing import List, Optional, Tuple, Union


        self.Command      = str
        self.Filename     = str
        self.Filepath     = str
        self.OptFilename  = Optional[str]
        self.OptFilepath  = Optional[str]
        self.OptMp3File   = Optional[str]
        self.OptMbpFile   = Optional[str]
        self.OptVideoFile = Optional[str]
        self.Info         = Union[int, str, bool]

        self.ListSentences= List[Tuple[
                str,
                str,
                self.OptVideoFile,
                self.OptMp3File,
                self.OptMbpFile
            ]
        ]


_tpal        = TypeAliases()
Filename     = _tpal.Filename
Filepath     = _tpal.Filepath
ListSentences= _tpal.ListSentences
OptFilename  = _tpal.OptFilename
OptFilepath  = _tpal.OptFilepath
OptMp3File   = _tpal.OptMp3File
OptMbpFile   = _tpal.OptMbpFile
OptVideoFile = _tpal.OptVideoFile
Info         = _tpal.Info
Command      = _tpal.Command
