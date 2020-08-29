# Asts
Asts (Another subs to srs) is a simple tool used to create cards to [Anki](http://ankisrs.net). It doesn't work on Windows yet.

# Dependencies

* [pysrt](https://pypi.org/project/pysrt/):
```
pip install pysrt
```

* Ffmpeg:
```
sudo pacman -S ffmpeg
```

* GTK3, PyGobject ([Only needed on Arch Linux](https://wiki.archlinux.org/index.php/GTK/Development#Python)):
```
sudo pacman -S gtk3 python-gobject
```

# Usage

1. Run the run.py
```
python run.py
```

2. Select the files needed (**A deck will be created if there is no deck with the name specified**)

![Screenshot-29-08-2020_15-09-10](https://user-images.githubusercontent.com/44977415/91643603-2dabe000-ea0b-11ea-8c12-36fd260aec48.png)



3. Select and edit the cards that you want add (**before adding cards certify that your anki is closed, it's not possible add new cards while anki still opened**)
![Screenshot-29-08-2020_16-02-56](https://user-images.githubusercontent.com/44977415/91644315-3f908180-ea11-11ea-8597-f2281d7f5f95.png)


## Anki Card Example (Front & Back)

![Screenshot-29-08-2020_16-03-24](https://user-images.githubusercontent.com/44977415/91644321-4cad7080-ea11-11ea-81a0-a0a783604876.png)

## Related Projects

Projects similar to [subs2srs](http://subs2srs.sourceforge.net/):

* [SubtitleMemorize](https://github.com/ChangSpivey/SubtitleMemorize)
* [substudy](https://github.com/emk/substudy)
* [movies2anki](https://github.com/kelciour/movies2anki)
