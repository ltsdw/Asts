# Asts
Asts (Another subs to srs) is a simple tool used to create [Anki](http://ankisrs.net) cards inspired by [subs2srs](http://subs2srs.sourceforge.net/). It doesn't work on Windows yet.

# Dependencies

* Ffmpeg:
   ```
   sudo pacman -S ffmpeg
   ```

* GTK3, PyGobject ([Only needed on Arch Linux](https://wiki.archlinux.org/index.php/GTK/Development#Python)):
   ```
   sudo pacman -S gtk3 python-gobject
   ```

# Usage

* 1 - Clone this repository:
   ```
   git clone --recursive https://github.com/ltsdw/Asts.git
   ```

* 2 - Change directory:
   ```
   cd Asts
   ```

* 3 - Run the run.py:
   ```
   python run.py
   ```

* 4 - Select the files needed:
   * **Obs:** A deck will be created if there is no deck with the name specified
   * Generally the collection.anki2 file is under ~/.local/share/Anki2/<profile name>

   ![image](https://user-images.githubusercontent.com/44977415/91675024-42729b80-eb11-11ea-8b95-6c285dd340c5.png)

* 5 - Select and edit the cards that you want add:
   * **Obs:** before adding cards certify that your anki is closed, it's not possible to add new cards while anki still opened
   ![image](https://user-images.githubusercontent.com/44977415/91822561-57812480-ec0e-11ea-9de3-908d0e3908ff.png)

## Anki Card Example (Front & Back)
   ![image](https://user-images.githubusercontent.com/44977415/91795910-5099e800-ebf5-11ea-8406-373bfcd1ec63.png)

## Library
   * [pysrt](https://github.com/byroot/pysrt)
   * [pyasstosrt](https://github.com/GitBib/pyasstosrt)

## Related Projects

Projects similar to [subs2srs](http://subs2srs.sourceforge.net/):

* [SubtitleMemorize](https://github.com/ChangSpivey/SubtitleMemorize)
* [substudy](https://github.com/emk/substudy)
* [movies2anki](https://github.com/kelciour/movies2anki)
