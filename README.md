# Asts
Asts (Another subs to srs) is a simple tool used to create [Anki](http://ankisrs.net) cards inspired by [subs2srs](http://subs2srs.sourceforge.net/). It doesn't work on Windows yet.

# Installing FFmpeg

Before using Asts ffmpeg must be installed and accessible at `$PATH` environment variable.
It can be installed from the official site [Download FFmpeg](https://ffmpeg.org/download.html).
Or it can be installed from via package manager from your distro.

* Arch Linux:
   ```
   sudo pacman -S ffmpeg
   ```

* Debian/Ubuntu
   ```
   sudo apt install ffmpeg
   ```

# Usage

* 1 - Clone this repository:
   ```
   git clone https://github.com/ltsdw/Asts.git
   ```

* 2 - Change directory:
   ```
   cd Asts
   ```

* 3 - Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

* 4 - Run the run-asts:
   ```
   ./run-asts
   ```

* 5 - Select the files needed:
   * A deck will be created if there is no deck with the name specified.
   * Generally the collection.anki2 file is under ~/.local/share/Anki2/<profile name>

   ![img-1](https://user-images.githubusercontent.com/44977415/139771271-b6fc7180-4e55-4587-b6a7-f1133b5dfd96.png)

* 6 - Select and edit the cards that you want add:
   * Before adding cards certify that your anki is **closed**, it's **not possible** to add new cards while anki still open.
   * It's possible edit both sides (front and back) before adding a card.

   ![img-2](https://user-images.githubusercontent.com/44977415/139771334-64cc1ce8-3d0f-40fd-b21e-15721f853f01.png)

## Anki Card Example (Front & Back)
   ![img-3](https://user-images.githubusercontent.com/44977415/139771380-7afbe41a-fef1-421e-a93f-2f1af9f8fb52.png)

## Libraries
   * [pysrt](https://github.com/byroot/pysrt): by [byroot](https://github.com/byroot), python parser for subrip (srt) files.
   * [pyasstosrt](https://github.com/GitBib/pyasstosrt) under [Apache-2.0 License](https://github.com/GitBib/pyasstosrt/blob/master/LICENSE): by [GitBib](https://github.com/GitBib), convert sub station alpha (ass) subtitle to srt format.

## Related Projects

Projects similar to [subs2srs](http://subs2srs.sourceforge.net/):

* [SubtitleMemorize](https://github.com/ChangSpivey/SubtitleMemorize)
* [substudy](https://github.com/emk/substudy)
* [movies2anki](https://github.com/kelciour/movies2anki)
