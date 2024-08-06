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
   * Generally the collection.anki2 file is under ~/.local/share/Anki2/<profile name>

   ![img-1](https://user-images.githubusercontent.com/44977415/139771271-b6fc7180-4e55-4587-b6a7-f1133b5dfd96.png)

* Select and edit the cards that you want add:
   * Before adding cards certify that your anki is **closed**, it's **not possible** to add new cards while anki still open.
   * It's possible edit both sides (front and back) before adding a card.

   ![img-2](https://user-images.githubusercontent.com/44977415/139771334-64cc1ce8-3d0f-40fd-b21e-15721f853f01.png)

## Anki Card Example (Front & Back)
   ![img-3](https://user-images.githubusercontent.com/44977415/139771380-7afbe41a-fef1-421e-a93f-2f1af9f8fb52.png)

## Related Projects

Projects similar to [subs2srs](http://subs2srs.sourceforge.net/):

* [SubtitleMemorize](https://github.com/ChangSpivey/SubtitleMemorize)
* [substudy](https://github.com/emk/substudy)
* [movies2anki](https://github.com/kelciour/movies2anki)
