"""This script is a rebased version of this one here: 
https://github.com/thinkle/gourmet/blob/master/gourmet/gtk_extras/pango_html.py
I'm not the author of this. All credits to Cydanil.
"""

from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple

from xml.etree.ElementTree  import fromstring

from gi.repository import Pango


class PangoToHtml(HTMLParser):
    """Decode a subset of Pango markup and serialize it as HTML.
    Only the Pango markup used within Gourmet is handled, although expanding it
    is not difficult.
    Due to the way that Pango attributes work, the HTML is not necessarily the
    simplest. For example italic tags may be closed early and reopened if other
    attributes, eg. bold, are inserted mid-way:
        <i> italic text </i><i><u>and underlined</u></i>
    This means that the HTML resulting from the conversion by this object may
    differ from the original that was fed to the caller.
    """
    def __init__(self):
        super().__init__()
        self.markup_text: str = ""  # the resulting content
        self.current_opening_tags: List[str] = []  # used during parsing
        self.current_closing_tags: List[str] = []  # used during parsing

        # The key is the Pango id of a tag, and the value is a tuple of opening
        # and closing html tags for this id.
        self.tags: Dict[str, Tuple[str, str]] = {}

    tag2html: Dict[str, Tuple[str, str]] = {
        Pango.Style.ITALIC.value_name: ("<i>", "</i>"),  # No <em> in Pango
        str(Pango.Weight.BOLD.real): ("<b>", "</b>"),
        Pango.Underline.SINGLE.value_name: ("<u>", "</u>"),
        "foreground-gdk": (r'<font color="{}">', "</font>"),
        "background-gdk": (r'<span style="background-color: rgb({});>', "</span>")
    }

    @staticmethod
    def pango_to_html_hex(val: str, span_style: bool = False) -> str:
        """Convert 32 bit Pango color hex string to 16 html.
        Pango string have the format 'ffff:ffff:ffff' (for white).
        These values get truncated to 16 bits per color into a single string:
        '#FFFFFF'.
        """

        red, green, blue = val.split(":")

        if not span_style:
            _red = hex(255 * int(red, base=16) // 65535)[2:].zfill(2)
            _green = hex(255 * int(green, base=16) // 65535)[2:].zfill(2)
            _blue = hex(255 * int(blue, base=16) // 65535)[2:].zfill(2)

            return f"#{_red}{_green}{_blue}"
        else:
            _red = (255 * int(red, base=16) // 65535)
            _green = (255 * int(green, base=16) // 65535)
            _blue = (255 * int(blue, base=16) // 65535)

            return f'{_red}, {_green}, {_blue}"'

    def feed(self, data: bytes) -> str:
        """Convert a buffer (text and and the buffer's iterators to html string.
        Unlike an HTMLParser, the whole string must be passed at once, chunks
        are not supported.
        """

        # Remove the Pango header: it contains a length mark, which we don't
        # care about, but which does not necessarily decodes as valid char.
        header_end = data.find(b"<text_view_markup>")
        data = data[header_end:].decode()

        # Get the tags
        tags_begin = data.index("<tags>")
        tags_end = data.index("</tags>") + len("</tags>")
        tags = data[tags_begin:tags_end]
        data = data[tags_end:]

        # Get the textual content, omitting the opening and closing text tags
        text_begin = data.index("<text>") + len("<text>")
        text_end = data.index("</text>")
        text = data[text_begin:text_end]

        # The remaining is serialized Pango footer, which we don't need.

        root            = fromstring(tags)
        tags_name       = list(root.iter('tag'))
        tags_attributes = list(root.iter('attr'))
        tags            = [ [tag_name, tag_attribute] for tag_name, tag_attribute in zip(tags_name, tags_attributes) ]
        tags_list = {}

        for tag in tags:
            opening_tags = ""
            closing_tags = ""

            tag_name    = tag[0].attrib['name']
            vtype       = tag[1].attrib['type']
            value       = tag[1].attrib['value'] 
            name        = tag[1].attrib['name']

            if vtype == "GdkColor":  # Convert colours to html
                if name in ['foreground-gdk', 'background-gdk']:
                    opening, closing = self.tag2html[name]
                    
                    if name == 'background-gdk':
                        hex_color = self.pango_to_html_hex(value, True)
                    else:
                        hex_color = self.pango_to_html_hex(value)

                    opening = opening.format(hex_color)
                else:
                    continue  # no idea!
            else:
                opening, closing = self.tag2html.get(value, ('', ''))

            opening_tags += opening
            closing_tags = closing + closing_tags   # closing tags are FILO

            tags_list[tag_name] = opening_tags, closing_tags

            if opening_tags:
                tags_list[tag_name] = opening_tags, closing_tags

        self.tags = tags_list

        # Create a single output string that will be sequentially appended to
        # during feeding of text. It can then be returned once we've parse all
        self.markup_text = ""
        self.current_opening_tags = []
        self.current_closing_tags = []

        super().feed(text)

        return self.markup_text

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        # The only tag in pango markup is "apply_tag". This could be ignored or
        # made an assert, but we let our parser quietly handle nonsense.
        if tag == "apply_tag":
            attrs = dict(attrs)
            tag_name = attrs.get('id')  # A tag may have a name, or else an id
            tag_name = attrs.get('name', tag_name)
            tags = self.tags.get(tag_name)

            if tags is not None:
                opening_tag, closing_tag = tags
                self.current_opening_tags.append(opening_tag)
                self.current_closing_tags.append(closing_tag)

    def handle_data(self, data: str) -> None:
        data = ''.join(self.current_opening_tags) + data
        self.current_opening_tags.clear()

        self.markup_text += data

    def handle_endtag(self, tag: str) -> None:
        if self.current_closing_tags:  # Can be empty due to pop in handle_data
            self.markup_text += self.current_closing_tags.pop()  # FILO

