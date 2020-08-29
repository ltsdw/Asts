# Asts
Asts (Another subs to srs) is a more simple project used to create cards with [Anki](http://ankisrs.net).

# Dependencies

* [pysrt](https://pypi.org/project/pysrt/):
```
pip install pysrt
```

* Ffmpeg
```
sudo pacman -S ffmpeg
```

* GTK3, PyGobject ([Only needed on Arch Linux](https://wiki.archlinux.org/index.php/GTK/Development#Python))
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
![Screenshot-29-08-2020_15-10-15](https://user-images.githubusercontent.com/44977415/91643628-7794c600-ea0b-11ea-992a-f65ebbbe61e6.png)


## Anki Card Example (Front & Back)

![Screenshot-29-08-2020_15-11-27](https://user-images.githubusercontent.com/44977415/91643684-d4907c00-ea0b-11ea-85c5-87c99dc1de12.png)
