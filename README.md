# Asts
Asts (Another subs to srs) is a simple tool used to create [Anki](http://ankisrs.net) cards inspired by [subs2srs](http://subs2srs.sourceforge.net/). It doesn't work on Windows yet.

# Requirements

Pip and FFMPEG must be installed and visible through the `$PATH` environment variable.
It can be installed from the official site [Pip installation](https://pip.pypa.io/en/stable/installation/) (pip most certainly is already installed) and [Download FFmpeg](https://ffmpeg.org/download.html), or they can be installed using the package manager from your distro.

* Arch Linux:
   ```
   sudo pacman -S ffmpeg python-pip
   ```

* Debian/Ubuntu
   ```
   sudo apt install ffmpeg python3-pip
   ```

# How to install

* Clone:
   ```
   git clone https://github.com/ltsdw/Asts.git
   ```

* Change to the directory:
   ```
   cd Asts
   ```

* Install the dependencies (only needed once):
   ```
   ./setup.sh
   ```

# How to use

* Run:
   ```
   ./run-asts
   ```

* Select the files needed:
   * A deck will be created if there is no deck with the name specified.
   * Usually the collection.anki2 file is under ~/.local/share/Anki2/*\<user name\>*/collection.anki2

   ![image1](https://github.com/user-attachments/assets/4703cbcc-03d1-4626-98a6-17b8b4b4149f)

* Select and edit the cards that you want add:
   * Before adding cards certify that your anki is **closed**, it's **not possible** to add new cards while anki still open.
   * It's possible edit both sides (front and back) before adding a card.

   ![image3](https://github.com/user-attachments/assets/51040ce4-dba5-4d09-b6c0-f00e69a7c1c3)

## Anki Card Example (Front & Back)
   ![image2](https://github.com/user-attachments/assets/18318999-ad2d-4ff7-b7fd-5033e19004bc)
   

## Related Projects

Projects similar to [subs2srs](http://subs2srs.sourceforge.net/):

* [SubtitleMemorize](https://github.com/ChangSpivey/SubtitleMemorize)
* [substudy](https://github.com/emk/substudy)
* [movies2anki](https://github.com/kelciour/movies2anki)
