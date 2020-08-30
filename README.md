# Asts
Asts (Another subs to srs) is a simple tool inspired by [subs2srs](http://subs2srs.sourceforge.net/) used to create [Anki](http://ankisrs.net) cards. It doesn't work on Windows yet.

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

1. Clone this repository:
```
git clone https://github.com/ltsdw/Asts.git
```

2. Change directory:
```
cd Asts
```

3. Run the run.py
```
python run.py
```

4. Select the files needed (**A deck will be created if there is no deck with the name specified**)

![image](https://user-images.githubusercontent.com/44977415/91649743-67053f80-ea4d-11ea-96a4-010026ebaf37.png)

5. Select and edit the cards that you want add (**before adding cards certify that your anki is closed, it's not possible to add new cards while anki still opened**)
![image](https://user-images.githubusercontent.com/44977415/91649768-c7947c80-ea4d-11ea-8c1c-e40cf3f7384b.png)

## Anki Card Example (Front & Back)

![image](https://user-images.githubusercontent.com/44977415/91649780-f3affd80-ea4d-11ea-8d9f-7c5bbb99928b.png)

## Related Projects

Projects similar to [subs2srs](http://subs2srs.sourceforge.net/):

* [SubtitleMemorize](https://github.com/ChangSpivey/SubtitleMemorize)
* [substudy](https://github.com/emk/substudy)
* [movies2anki](https://github.com/kelciour/movies2anki)
