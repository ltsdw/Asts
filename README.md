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
   * A deck will be created if there is no deck with the name specified.
   * Generally the collection.anki2 file is under ~/.local/share/Anki2/<profile name>

   ![image](https://user-images.githubusercontent.com/44977415/91675024-42729b80-eb11-11ea-8b95-6c285dd340c5.png)

* 5 - Select and edit the cards that you want add:
   * Before adding cards certify that your anki is **closed**, it's **not possible** to add new cards while anki still opened.
   * It's possible edit both sides (front and back) before adding a card.
   ![Screenshot-07-09-2020_02-02-42](https://user-images.githubusercontent.com/44977415/92350160-7a985200-f0ae-11ea-8690-d64e43deb563.png)

## Anki Card Example (Front & Back)
   ![Screenshot-07-09-2020_02-03-16](https://user-images.githubusercontent.com/44977415/92350208-a61b3c80-f0ae-11ea-8d06-b4e17b39e95a.png)

## Libraries
   * [pysrt](https://github.com/byroot/pysrt): by [byroot](https://github.com/byroot), python parser for subrip (srt) files.
   * [pyasstosrt](https://github.com/GitBib/pyasstosrt) under [Apache-2.0 License](https://github.com/GitBib/pyasstosrt/blob/master/LICENSE): by [GitBib](https://github.com/GitBib), convert sub station alpha (ass) subtitle to srt format.

## Related Projects

Projects similar to [subs2srs](http://subs2srs.sourceforge.net/):

* [SubtitleMemorize](https://github.com/ChangSpivey/SubtitleMemorize)
* [substudy](https://github.com/emk/substudy)
* [movies2anki](https://github.com/kelciour/movies2anki)
