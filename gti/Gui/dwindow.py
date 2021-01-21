from gi import require_version
require_version('Gtk', '3.0')

from gi.repository      import Gtk, Gdk, GLib, Pango
from os                 import path, system
from anki               import Collection as aopen
from anki.rsbackend     import DBError
from threading          import Thread
from concurrent.futures import ThreadPoolExecutor
from multiprocessing    import Manager, Lock
from uuid               import uuid1

from ..Funcs import (
        checkIfIsCollection,
        checkIfIsVideo, 
        checkIfIsAss,
        checkIfIsSrt,
        checkIfIsSub,
        checkIfIsSubOpt,
        clearCachedFiles,
        createCacheDirIfItNotExists,
        cut,
        giveMe1Tuple,
        openSubFile,
        subExtractReturnTuple,
        writeRecentUsedCached,
        serializeIt,
        deserializeIt,
        PangoToHtml
        )

glade_file  = path.join((path.abspath('gti/Gui/glade')) + '/' + 'gui_final.glade')
builder     = Gtk.Builder()
builder.add_from_file(glade_file)

class MyThread(Thread):
    def __init__(
                self, updateProgress,
                sub_list_store, vid_filename,
                sub_list_store_back,
                coll_filename, deck_name,
                tuple_of_medias,
                tuple_of_sentences,
                callDialogAnki):

        Thread.__init__(self)

        self.callback                   = updateProgress

        self.sub_list_store             = sub_list_store
        self.vid_filename               = vid_filename
        self.sub_list_store_back        = sub_list_store_back
        self.coll_filename              = coll_filename
        self.deck_name                  = deck_name
        self.tuple_of_medias            = tuple_of_medias
        self.tuple_of_sentences         = tuple_of_sentences

        self.callDialogAnki             = callDialogAnki

    #Normally this functions wouldn't be here, but I need them to display a progress bar correctly
    def cutMedias(self, vid_filename, tuple_of_medias):
        manager = Manager()
        lock    = manager.Lock()

        with ThreadPoolExecutor() as executor:
            for media in tuple_of_medias:
                executor.submit(cut, vid_filename, media, lock, self.callback)

    def writeCards(self, tuple_of_sentence, deck, lock):
        with lock:
            try:
                (sentence_front, sentence_back, video_audio)         = tuple_of_sentence
                # Case only snapshot is selected
                if video_audio.split('.')[-1] == 'bmp': 
                    image = media_video_audio = video_audio 
                    media_image         = self.deck.media.addFile(self.cache_dir + '/' + image)
                else:
                    image = None
                    media_video_audio   = self.deck.media.addFile(self.cache_dir + '/' + video_audio)

            except ValueError:
                (sentence_front, sentence_back, video_audio, image) = tuple_of_sentence

                media_video_audio   = self.deck.media.addFile(self.cache_dir + '/' + video_audio)
                media_image         = self.deck.media.addFile(self.cache_dir + '/' + image)

            sentence_front      = sentence_front.replace('\n', '<br>')
            sentence_back       = sentence_back.replace('\n', '<br>')
            card                = self.deck.newNote()
            ext_of_media        = media_video_audio.split('.')[-1]
            
            if 'mp3' in ext_of_media and not image:
                card['Front']   = sentence_front                    +   '<br><br>'  + f'[sound:{media_video_audio}]'
                card['Back']    = sentence_back
            
            elif 'mp4' in ext_of_media and not image:
                card['Front']   = sentence_front
                card['Back']    = f'[sound:{media_video_audio}]'    +   '<br><br>'  + sentence_back
            
            elif 'mp3' in ext_of_media and image:
                card['Front']   = sentence_front                    +   '<br><br>'  + f'[sound:{media_video_audio}]'
                card['Back']    = f'<img src="{media_image}">'      +   '<br><br>'  + sentence_back

            else:
                card['Front']   = sentence_front
                card['Back']    = f'<img src="{media_image}">'      +   '<br><br>'  + sentence_back

            self.deck.addNote( card )
            self.deck.save()

            GLib.idle_add(self.callback)

    def makeCards(self, coll_filename, deck_name, tuple_of_sentences):
        card_type = 'Basic'
        self.cache_dir = path.abspath('data/cache/media')
        self.deck = aopen( coll_filename )
        deck_id = self.deck.decks.id( deck_name )
        self.deck.decks.select( deck_id )
        model = self.deck.models.byName( card_type )
        model['did'] = deck_id
        self.deck.models.save( model )
        self.deck.models.setCurrent( model )

        manager = Manager()
        lock = manager.Lock()

        with ThreadPoolExecutor() as executor:
            for tuple_of_sentence in tuple_of_sentences:
                executor.submit(self.writeCards, tuple_of_sentence, self.deck, lock)

        self.deck.close()

    def run(self):
        clearCachedFiles()

        self.cutMedias(self.vid_filename, self.tuple_of_medias)

        #This will call a function that will draw a dialog window case anki is already opened
        try:
            self.makeCards(self.coll_filename, self.deck_name, self.tuple_of_sentences)
        except DBError:
            GLib.idle_add(self.callDialogAnki)

        clearCachedFiles()


class Handler(object):

    def __init__(self):
        super(Handler, self)

        #calling this to clear cached before doing anything, to certify that there's no file in case the cache wasn't properly cleared
        clearCachedFiles()

        createCacheDirIfItNotExists()

        self.current                    = 0
        self.collection_file            = builder.get_object('collection_file')
        self.video_file                 = builder.get_object('video_file')
        self.video_sub_file             = builder.get_object('video_sub_file')
        self.video_sub_file_optional    = builder.get_object('video_sub_file_optional')
        self.deck_name_entry            = builder.get_object('deck_name_entry') 

        try:
            cache_dir       = path.abspath('data/cache')
            cached_usage    = path.join(cache_dir + '/' + 'cached_usage.txt') 
            with open(cached_usage, 'r') as f:
                list_cache = f.read().split('\n')
            self.collection_file.set_filename(list_cache[0])
            self.deck_name_entry.set_text(list_cache[1])
        except FileNotFoundError:
            pass

        self.button = builder.get_object('proceed_action')

        coll_file_filter = Gtk.FileFilter()
        coll_file_filter.set_name('collection.anki2')
        coll_file_filter.add_pattern('*.anki2')
        self.collection_file.add_filter(coll_file_filter)

        vid_file_filter = Gtk.FileFilter()
        vid_file_filter.set_name('Video File')
        vid_file_filter.add_mime_type('video/mp4')
        vid_file_filter.add_mime_type('video/wmv')
        vid_file_filter.add_mime_type('video/avi')
        vid_file_filter.add_mime_type('video/mkv')
        vid_file_filter.add_mime_type('video/webm')
        vid_file_filter.add_pattern('*.mp4')
        vid_file_filter.add_pattern('*.wmv')
        vid_file_filter.add_pattern('*.avi')
        vid_file_filter.add_pattern('*.mkv')
        vid_file_filter.add_pattern('*.webm')
        self.video_file.add_filter(vid_file_filter)

        sub_file_filter = Gtk.FileFilter()
        sub_file_filter.set_name('Subtitles (ASS/SRT)')
        sub_file_filter.add_pattern('*.srt')
        sub_file_filter.add_pattern('*.ass')
        self.video_sub_file.add_filter(sub_file_filter)
        self.video_sub_file_optional.add_filter(sub_file_filter)

        GLib.timeout_add(300, self.setSensitiveProceedButton, None)
        
        self.second_window_hided = False
        self.second_window = builder.get_object('second_window')

    def setSensitiveProceedButton(self, *args):
        coll_filename           = self.collection_file.get_filename()
        vid_filename            = self.video_file.get_filename()
        vid_sub_filename        = self.video_sub_file.get_filename()
        vid_sub_filename_opt    = self.video_sub_file_optional.get_filename()
        deck_name               = self.deck_name_entry.get_text()

        if all(( checkIfIsCollection(coll_filename),
                 checkIfIsVideo(vid_filename),
                 checkIfIsSub(vid_sub_filename),
                 checkIfIsSubOpt(vid_sub_filename_opt),)) and deck_name != '':
            if checkIfIsSrt(vid_sub_filename) == True == checkIfIsAss(vid_sub_filename_opt) \
            or checkIfIsAss(vid_sub_filename) == True == checkIfIsSrt(vid_sub_filename_opt):
                self.button.set_sensitive(False)
            elif checkIfIsAss(vid_sub_filename) == True == checkIfIsAss(vid_sub_filename_opt) and checkIfIsSubOpt(vid_sub_filename_opt):
                self.button.set_sensitive(True)
            elif checkIfIsSrt(vid_sub_filename) == True == checkIfIsSrt(vid_sub_filename_opt) and checkIfIsSubOpt(vid_sub_filename_opt):
                self.button.set_sensitive(True)
            elif checkIfIsAss(vid_sub_filename) and checkIfIsSubOpt(vid_sub_filename_opt):
                self.button.set_sensitive(True)
            elif checkIfIsSrt(vid_sub_filename) and checkIfIsSubOpt(vid_sub_filename_opt):
                self.button.set_sensitive(True)
            else:
                self.button.set_sensitive(False)
        else:
            self.button.set_sensitive(False)

        return True

    def on_dellcoll_clicked(self, *args):
       self.collection_file.unselect_all()

    def on_dellvid_clicked(self, *args):
        self.video_file.unselect_all()

    def on_dellsub_clicked(self, *args):
        self.video_sub_file.unselect_all()

    def on_dellsubopt_clicked(self, *args):
        self.video_sub_file_optional.unselect_all()

    def on_proceed_action_clicked(self, *args):
        text_view_front                 = builder.get_object('text_view_front') 
        text_view_back                  = builder.get_object('text_view_back')
        self.conclude_process_button    = builder.get_object('conclude_process')
        self.search_entry               = builder.get_object('search_entry')
        self.text_buffer_front          = text_view_front.get_buffer()
        self.text_buffer_back           = text_view_back.get_buffer()

        self.coll_filename          = self.collection_file.get_filename()
        self.vid_filename           = self.video_file.get_filename()
        self.vid_sub_filename       = self.video_sub_file.get_filename()
        self.vid_sub_filename_opt   = self.video_sub_file_optional.get_filename()
        self.deck_name              = self.deck_name_entry.get_text()

        self.open_sub_file          = openSubFile(self.vid_sub_filename)
        self.sub_tree_view          = builder.get_object('sub_tree_view')
        self.sub_list_store         = Gtk.ListStore(int, str, str, str, bool, bool, bool)

        writeRecentUsedCached(self.coll_filename, self.deck_name)

        #   Despite of  the only values that are importante in self.sub_list_store_back
        # are the first value (int) and the second value (str)
        # but I need populate it with the other values because the fuction return them, but on the back
        # it doesn't have any use.
        self.sub_list_store_back = Gtk.ListStore(int, str, str, str, bool, bool, bool)

        self.selected_row = self.sub_tree_view.get_selection()
        self.selected_row.connect("changed", self.item_selected)

        #   Checking if is the first time that is window is generated
        # this prevent drawing duplicated elements
        if not self.second_window_hided:

            for i, title in enumerate(['Indice', 'Dialog']):
                renderer = Gtk.CellRendererText()
                path_column = Gtk.TreeViewColumn(title=title, cell_renderer=renderer, text=i)
                if title == 'Dialog':
                    path_column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
                    path_column.set_fixed_width(520)
                    path_column.set_min_width(520)
                self.sub_tree_view.append_column(path_column)

            # Making some cells editable 'Start' and 'End' respectivily
            editable_start_field = Gtk.CellRendererText()
            editable_end_field = Gtk.CellRendererText()
            editable_start_field.set_property('editable', True)
            editable_end_field.set_property('editable', True)
            path_column_editable = Gtk.TreeViewColumn(title='Start', cell_renderer=editable_start_field, text=2)
            self.sub_tree_view.append_column(path_column_editable)
            path_column_editable = Gtk.TreeViewColumn(title='End', cell_renderer=editable_end_field, text=3)
            self.sub_tree_view.append_column(path_column_editable)
            editable_start_field.connect('edited', self.start_field)
            editable_end_field.connect('edited', self.end_field)

            # cell video, audio and snapshot to toggle
            self.renderer_video_toggle = Gtk.CellRendererToggle()
            column_toggle = Gtk.TreeViewColumn(title='Video', cell_renderer=self.renderer_video_toggle, active=4)
            self.sub_tree_view.append_column(column_toggle)
            self.renderer_video_toggle.connect("toggled", self.on_cell_video_toggled)

            self.renderer_audio_toggle = Gtk.CellRendererToggle()
            column_toggle = Gtk.TreeViewColumn(title='Audio', cell_renderer=self.renderer_audio_toggle, active=5)
            self.sub_tree_view.append_column(column_toggle)
            self.renderer_audio_toggle.connect("toggled", self.on_cell_audio_toggled)

            self.renderer_snapshot_toggle = Gtk.CellRendererToggle()
            column_toggle = Gtk.TreeViewColumn(title='Snapshot', cell_renderer=self.renderer_snapshot_toggle, active=6)
            self.sub_tree_view.append_column(column_toggle)
            self.renderer_snapshot_toggle.connect("toggled", self.on_cell_snapshot_toggled)

            # Toolbar
            toolbar                = builder.get_object('toolbar')

            toolbar.insert(Gtk.SeparatorToolItem(), 0)

            set_color_button   = Gtk.ToolButton()
            set_color_button.set_icon_name('gtk-select-color')
            toolbar.insert(set_color_button, 1)

            tool_item_color_button  = Gtk.ToolItem()
            self.color_button       = Gtk.ColorButton()
            tool_item_color_button.add(self.color_button)
            toolbar.insert(tool_item_color_button, 2)
            set_color_button.connect('clicked', self.on_toolbar_color_button_clicked)

            toolbar.insert(Gtk.SeparatorToolItem(), 3)

            tag_underline_front     = self.text_buffer_front.create_tag('underline',    underline=Pango.Underline.SINGLE)
            tag_bold_front          = self.text_buffer_front.create_tag('bold',         weight=Pango.Weight.BOLD)
            tag_italic_front        = self.text_buffer_front.create_tag('italic',       style=Pango.Style.ITALIC)

            tag_underline_back      = self.text_buffer_back.create_tag('underline',     underline=Pango.Underline.SINGLE)
            tag_bold_back           = self.text_buffer_back.create_tag('bold',          weight=Pango.Weight.BOLD)
            tag_italic_back         = self.text_buffer_back.create_tag('italic',        style=Pango.Style.ITALIC)

            button_underline        = Gtk.ToolButton()
            button_underline.set_icon_name('format-text-underline-symbolic')
            toolbar.insert(button_underline, 4)
            button_underline.connect('clicked', self.on_toolbar_tag_button_clicked, tag_underline_front, tag_underline_back)

            button_bold             = Gtk.ToolButton()
            button_bold.set_icon_name('format-text-bold-symbolic')
            toolbar.insert(button_bold, 5)
            button_bold.connect('clicked', self.on_toolbar_tag_button_clicked, tag_bold_front, tag_bold_back)

            button_italic           = Gtk.ToolButton()
            button_italic.set_icon_name('format-text-italic-symbolic')
            toolbar.insert(button_italic, 6)
            button_italic.connect('clicked', self.on_toolbar_tag_button_clicked, tag_italic_front, tag_italic_back)

            toolbar.insert(Gtk.SeparatorToolItem(), 7)

            button_remove_all_tags  = Gtk.ToolButton()
            button_remove_all_tags.set_icon_name('edit-clear-symbolic')
            toolbar.insert(button_remove_all_tags, 8)
            button_remove_all_tags.connect('clicked', self.on_button_remove_all_tags_clicked)

            toolbar.insert(Gtk.SeparatorToolItem(), 9)

        ### From here everything is generated even if the window is hided
        for i in range(len(self.open_sub_file)):

            if subExtractReturnTuple(giveMe1Tuple(self.open_sub_file[i])):
                self.sub_list_store.append(subExtractReturnTuple(giveMe1Tuple(self.open_sub_file[i])))

        if self.vid_sub_filename_opt:
            self.open_sub_file_opt = openSubFile(self.vid_sub_filename_opt)
            
            #   I don't know how to handle a optional input with differents lenght over the vid_sub_filename
            # so this one here will fill the back with nothing when it's get lost
            for i in range(len(self.open_sub_file)):
                try:
                    self.sub_list_store_back.append(subExtractReturnTuple(giveMe1Tuple(self.open_sub_file_opt[i])))
                except IndexError:
                    self.sub_list_store_back.append((i, '', '', '', False, False, False))                   
        else:
            self.sub_list_store_back = Gtk.ListStore(int, str)
            for i in range(len(self.open_sub_file)):
                self.sub_list_store_back.append((i, ''))

        # setting the model after all the lists are already populated
        self.sub_tree_view.set_model(self.sub_list_store)

        #   The key value need to be a string to be used correctly when the value of 'path' is passed to the dictionary
        # otherwise if the 'key' is a int() the value will be assign at wrong place when passed 'path' as a key, even though the path value is correct
        self.dict_any       = {str(key): False for key in range(len(self.sub_list_store))}
        self.any_toggled    = False

        # dictionary to track the tags
        self.dict_any_change_front  =   {str(key): serializeIt(text_buffer=self.text_buffer_front, tmp_string=value[1]) \
                                        for key, value in enumerate(self.sub_list_store)}
        self.dict_any_change_back   =   {str(key): serializeIt(text_buffer=self.text_buffer_back, tmp_string=value[1]) \
                                        for key, value in enumerate(self.sub_list_store_back)}
        self.second_window.show_all()

        # Sensitive to the conclude_process_button
        GLib.timeout_add(300, self.setSensitiveConcludeProcess, None)

        self.search_entry.connect('changed', self.searchIt)

    def item_selected(self, *args):
        #   Silencing a indexerror that will occur in case the window was hided and rised again
        # it is not important, can be ignored

        try:
            path                    = str(self.selected_row.get_selected_rows()[1][0])

            deserializeIt(self.text_buffer_front, self.dict_any_change_front[path])
            deserializeIt(self.text_buffer_back, self.dict_any_change_back[path])
            self.text_buffer_front.connect('changed', self.editingCard)
            self.text_buffer_back.connect('changed', self.editingCardBack)

        except IndexError:
            pass

    def editingCard(self, text_buffer_front):
        #   Silencing a indexerror that will occur in case the window was hided and rised again
        # it is not important, can be ignored
        try:
            path                                        = self.selected_row.get_selected_rows()[1][0]
            start_iter_front                            = text_buffer_front.get_start_iter()
            end_iter_front                              = text_buffer_front.get_end_iter() 
            self.sub_list_store[path][1]                = text_buffer_front.get_text(start_iter_front, end_iter_front, True)

            self.dict_any_change_front[str(path)]       = serializeIt(text_buffer=text_buffer_front)

        except IndexError:
            pass

    def editingCardBack(self, text_buffer_back):
        #   Silencing a indexerror that will occur in case the window was hided and rised again
        # it is not important, can be ignored
        try:
            path                                        = self.selected_row.get_selected_rows()[1][0]
            start_iter_back                             = text_buffer_back.get_start_iter()
            end_iter_back                               = text_buffer_back.get_end_iter() 
            self.sub_list_store_back[path][1]           = text_buffer_back.get_text(start_iter_back, end_iter_back, True)

            self.dict_any_change_back[str(path)]        = serializeIt(text_buffer=text_buffer_back)

        except IndexError:
            pass

    def start_field(self, widget, path, text):
        self.sub_list_store[path][2] = text

    def end_field(self, widget, path, text):
        self.sub_list_store[path][3] = text

    def on_toolbar_color_button_clicked(self, widget):
        #   Silencing a indexerror that will occur in case the window was hided and rised again
        # it is not important, can be ignored
        try:
            path            = str(self.selected_row.get_selected_rows()[1][0])
            
            color           = self.color_button.get_color().to_string()
            bounds_front    = self.text_buffer_front.get_selection_bounds()
            bounds_back     = self.text_buffer_back.get_selection_bounds()
            tag_table_front = self.text_buffer_front.get_tag_table()
            tag_table_back  = self.text_buffer_back.get_tag_table()

            ##### FRONT
            if len(bounds_front) != 0:
                (start, end)        = bounds_front
                selection_front     = self.text_buffer_front.get_text(start, end, True)
                get_insert_front    = self.text_buffer_front.get_insert()

                if not tag_table_front.lookup(color):
                    tag_front       = self.text_buffer_front.create_tag(color, foreground=color)
                    self.text_buffer_front.apply_tag(tag_front, start, end)
                else:
                    self.text_buffer_front.apply_tag_by_name(color, start, end)
    
                self.dict_any_change_front[path] = serializeIt(text_buffer=self.text_buffer_front)

            ###### BACK
            if len(bounds_back) != 0:
                (start, end)        = bounds_back
                selection_back      = self.text_buffer_back.get_text(start, end, True)
                get_insert_back     = self.text_buffer_back.get_insert()

                if not tag_table_back.lookup(color):
                    tag_back       = self.text_buffer_back.create_tag(color, foreground=color)
                    self.text_buffer_back.apply_tag(tag_back, start, end)
                else:
                    self.text_buffer_back.apply_tag_by_name(color, start, end)

                self.dict_any_change_back[path] = serializeIt(text_buffer=self.text_buffer_back)

        except IndexError:
            pass

    def on_toolbar_tag_button_clicked(self, widget, tag_front, tag_back):
        #   Silencing a indexerror that will occur in case the window was hided and rised again
        # it is not important, can be ignored
        try:
            path        = str(self.selected_row.get_selected_rows()[1][0])

            bounds_front    = self.text_buffer_front.get_selection_bounds()
            bounds_back     = self.text_buffer_back.get_selection_bounds()

            ##### FRONT
            if len(bounds_front) != 0:
                (start, end)        = bounds_front
                selection_front     = self.text_buffer_front.get_text(start, end, True)
                get_insert_front    = self.text_buffer_front.get_insert()

                self.text_buffer_front.apply_tag(tag_front, start, end)

                self.dict_any_change_front[path] = serializeIt(text_buffer=self.text_buffer_front)

            ###### BACK
            if len(bounds_back) != 0:
                (start, end)        = bounds_back
                selection_back      = self.text_buffer_back.get_text(start, end, True)
                get_insert_back     = self.text_buffer_back.get_insert()

                self.text_buffer_back.apply_tag(tag_back, start, end)

                self.dict_any_change_back[path] = serializeIt(text_buffer=self.text_buffer_back)

        except IndexError:
            pass

    def on_button_remove_all_tags_clicked(self, widget):
        start_iter_front    = self.text_buffer_front.get_start_iter()
        end_iter_front      = self.text_buffer_front.get_end_iter()

        start_iter_back     = self.text_buffer_back.get_start_iter()
        end_iter_back       = self.text_buffer_back.get_end_iter()

        self.text_buffer_front.remove_all_tags(start_iter_front, end_iter_front)
        self.text_buffer_back.remove_all_tags(start_iter_back, end_iter_back)

    def on_cell_video_toggled(self, widget, path):
        if self.sub_list_store[path][5]:
            self.sub_list_store[path][5]    = not self.sub_list_store[path][5]
            self.sub_list_store[path][4]    = not self.sub_list_store[path][4] 
            self.dict_any[str(path)]        = self.sub_list_store[path][4]
        elif self.sub_list_store[path][6]:
            self.sub_list_store[path][6]    = not self.sub_list_store[path][6]
            self.sub_list_store[path][4]    = not self.sub_list_store[path][4]
            self.dict_any[str(path)]        = self.sub_list_store[path][4]
        else:
            self.sub_list_store[path][4]    = not self.sub_list_store[path][4]
            self.dict_any[str(path)]        = self.sub_list_store[path][4]

        if True in self.dict_any.values():
            self.any_toggled = True
        else:
            self.any_toggled = False

    def on_cell_audio_toggled(self, widget, path):
        if self.sub_list_store[path][4]:
            self.sub_list_store[path][4]    = not self.sub_list_store[path][4]
            self.sub_list_store[path][5]    = not self.sub_list_store[path][5] 
            self.dict_any[str(path)]        = self.sub_list_store[path][5]
        elif self.sub_list_store[path][5] and self.sub_list_store[path][6]:
            self.sub_list_store[path][5]    = not self.sub_list_store[path][5]
            self.dict_any[str(path)]        = self.sub_list_store[path][6]
        else:
            self.sub_list_store[path][5]    = not self.sub_list_store[path][5]
            self.dict_any[str(path)]        = self.sub_list_store[path][5]

        if True in self.dict_any.values():
            self.any_toggled = True
        else:
            self.any_toggled = False

    def on_cell_snapshot_toggled(self, widget, path):
        if self.sub_list_store[path][4]:
            self.sub_list_store[path][4]    = not self.sub_list_store[path][4]
            self.sub_list_store[path][6]    = not self.sub_list_store[path][6] 
            self.dict_any[str(path)]        = self.sub_list_store[path][6]
        elif self.sub_list_store[path][6] and self.sub_list_store[path][5]:
            self.sub_list_store[path][6]    = not self.sub_list_store[path][6]
            self.dict_any[str(path)]        = self.sub_list_store[path][5]
        else:
            self.sub_list_store[path][6]    = not self.sub_list_store[path][6]
            self.dict_any[str(path)]        = self.sub_list_store[path][6]

        if True in self.dict_any.values():
            self.any_toggled = True
        else:
            self.any_toggled = False

    def on_select_all_video_toggled(self, *args):
        for i in range(len(self.sub_list_store)):
            if self.sub_list_store[i][5]:
                self.sub_list_store[i][5]   = not self.sub_list_store[i][5]
                self.sub_list_store[i][4]   = not self.sub_list_store[i][4]
                self.dict_any[str(i)]       = self.sub_list_store[i][4]
            elif self.sub_list_store[i][6]:
                self.sub_list_store[i][6]   = not self.sub_list_store[i][6]
                self.sub_list_store[i][4]   = not self.sub_list_store[i][4]
                self.dict_any[str(i)]       = self.sub_list_store[i][4]
            else:
                self.sub_list_store[i][4]   = not self.sub_list_store[i][4]
                self.dict_any[str(i)]       = self.sub_list_store[i][4]

        if True in self.dict_any.values():
            self.any_toggled = True
        else:
            self.any_toggled = False

    def on_select_all_audio_toggled(self, *args):
        for i in range(len(self.sub_list_store)):
            if self.sub_list_store[i][4]:
                self.sub_list_store[i][4]   = not self.sub_list_store[i][4]
                self.sub_list_store[i][5]   = not self.sub_list_store[i][5]
                self.dict_any[str(i)]       = self.sub_list_store[i][5]
            elif self.sub_list_store[i][5] and self.sub_list_store[i][6]:
                self.sub_list_store[i][5]   = not self.sub_list_store[i][5]
                self.dict_any[str(i)]       = self.sub_list_store[i][6]
            else:
                self.sub_list_store[i][5]   = not self.sub_list_store[i][5]
                self.dict_any[str(i)]       = self.sub_list_store[i][5]

        if True in self.dict_any.values():
            self.any_toggled = True
        else:
            self.any_toggled = False

    def on_select_all_snapshot_checkbutton_toggled(self, *args):
        for i in range(len(self.sub_list_store)):
            if self.sub_list_store[i][4]:
                self.sub_list_store[i][4]   = not self.sub_list_store[i][4]
                self.sub_list_store[i][6]   = not self.sub_list_store[i][6]
                self.dict_any[str(i)]       = self.sub_list_store[i][6]
            else:
                self.sub_list_store[i][6]   = not self.sub_list_store[i][6]
                self.dict_any[str(i)]       = self.sub_list_store[i][6]

        if True in self.dict_any.values():
            self.any_toggled = True
        else:
            self.any_toggled = False

    #Normally this type of function wouldn't be here, but I need it to display the progress correctly
    def tupleMedias(self, sub_list_store, sub_list_store_back):
        self.tuple_of_sentences = ()
        self.tuple_of_medias    = ()
        p                       = PangoToHtml()
        for i in range(len(self.sub_list_store)):
            if self.sub_list_store[i][4] or self.sub_list_store[i][5] or self.sub_list_store[i][6]:
                #   A unique id for each media, some images will conflict if it has the same name as a image
                # on anki media collection 
                uuid_media  = uuid1().int

                text_front  = p.feed(self.dict_any_change_front[str(i)])
                text_back   = p.feed(self.dict_any_change_back[str(i)])
                self.tuple_of_medias = self.tuple_of_medias + ( tuple([uuid_media] + self.sub_list_store[i][1:]),)

                if self.sub_list_store[i][4] and self.sub_list_store[i][6]:
                    self.tuple_of_sentences = self.tuple_of_sentences + ((  text_front,
                                                                            text_back,
                                                                            f'{uuid_media}.mp4',
                                                                            f'{uuid_media}.bmp'),)
                elif self.sub_list_store[i][5] and self.sub_list_store[i][6]:
                    self.tuple_of_sentences = self.tuple_of_sentences + ((  text_front,
                                                                            text_back,
                                                                            f'{uuid_media}.mp3',
                                                                            f'{uuid_media}.bmp'),)
                elif self.sub_list_store[i][4] and not self.sub_list_store[i][6]:
                    self.tuple_of_sentences = self.tuple_of_sentences + ((  text_front,
                                                                            text_back,
                                                                            f'{uuid_media}.mp4'),)
                elif self.sub_list_store[i][5] and not self.sub_list_store[i][6]:
                    self.tuple_of_sentences = self.tuple_of_sentences + ((  text_front,
                                                                            text_back,
                                                                            f'{uuid_media}.mp3'),)
                else:
                    self.tuple_of_sentences = self.tuple_of_sentences + ((  text_front,
                                                                            text_back,
                                                                            f'{uuid_media}.bmp'),)

    def setSensitiveConcludeProcess(self, *args):
        if self.any_toggled:
            self.conclude_process_button.set_sensitive(True)
        else:
            self.conclude_process_button.set_sensitive(False)

        return True

    def on_conclude_process_clicked(self, *args):
        self.conclude_process_button.set_sensitive(False)

        self.tupleMedias(self.sub_list_store, self.sub_list_store_back)
        thread = MyThread(
                self.updateProgress,
                self.sub_list_store,
                self.vid_filename,
                self.sub_list_store_back,
                self.coll_filename,
                self.deck_name,
                self.tuple_of_medias,
                self.tuple_of_sentences,
                self.callDialogAnki)

        thread.start()
 
    def updateProgress(self):
        self.current    = self.current + 1
        maximum         = (len(self.tuple_of_medias) + len(self.tuple_of_sentences))
        progress_bar    = builder.get_object('progress_bar')
        button          = builder.get_object('conclude_process')
        progress_bar.set_fraction(self.current / maximum)

        if self.current == maximum:
            progress_bar.set_text('Concluded!')
            self.conclude_process_button.set_sensitive(True)
            progress_bar.set_show_text(True)
            self.current = 0
        else:
            self.button.set_sensitive(False)
            progress_bar.set_show_text(False)

        return False

    def searchIt(self, search_entry):
        term_searched = self.search_entry.get_text()
        for i, term in enumerate(self.sub_list_store):
            if term_searched in term[1].lower() and not term_searched == '':
                self.sub_tree_view.set_cursor(i)
                break

    def on_cancel_process_clicked(self, *args):
        self.conclude_process_button.set_sensitive(True)

        self.second_window_hided = True
        self.second_window.hide()
        progress_bar = builder.get_object('progress_bar')
        progress_bar.set_fraction(0)
        progress_bar.set_show_text(False)

        self.current = 0

    def on_second_window_destroy_event(self, *args):
        self.on_cancel_process_clicked()

    def on_second_window_destroy(self, *args):
        self.on_cancel_process_clicked()

    def callDialogAnki(self, *args):
        clearCachedFiles()
        progress_bar                    = builder.get_object('progress_bar') 
        anki_open_window                = builder.get_object('anki_open_window')
        self.conclude_process_button    = builder.get_object('conclude_process')

        self.conclude_process_button.set_sensitive(False)
        progress_bar.set_show_text(False)
        progress_bar.set_fraction(0)
        anki_open_window.show_all()

        self.current = 0

    def on_ok_anki_open_clicked(self, *args):
        anki_open_window = builder.get_object('anki_open_window')
        self.conclude_process_button.set_sensitive(True)
        anki_open_window.hide()

    def on_main_destroy(self, *args):
        Gtk.main_quit()

    def on_cancel_action_clicked(self, *args):
        Gtk.main_quit()


def main():
    builder.connect_signals(Handler())
    window = builder.get_object('main')
    window.show_all()
    Gtk.main()

