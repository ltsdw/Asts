#! /bin/python

from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
from os import path, system
from anki import Collection as aopen
import threading

from ..Funcs import (
        checkIfIsCollection,
        checkIfIsVideo,
        checkIfIsSrt,
        checkIfIsSrtOpt,
        clearCachedFiles,
        createCacheDirIfItNotExists,
        cut,
        giveMe1Tuple,
        #makeCards,
        openSrtFile,
        subExtractReturnTuple,
        writeRecentUsedCached
)

glade_file = path.join((path.abspath('gti/Gui/glade')) + '/' + 'gui_final.glade')
builder = Gtk.Builder()
builder.add_from_file(glade_file)

class MyThread(threading.Thread):
    def __init__(self, cllbck, s_list_store, v_filename, s_list_store_back, c_filename, d_name, t_of_medias, t_of_sentences):
        threading.Thread.__init__(self)

        self.callback               = cllbck

        self.sub_list_store         = s_list_store
        self.vid_filename           = v_filename
        self.sub_list_store_back    = s_list_store_back
        self.coll_filename          = c_filename
        self.deck_name              = d_name
        self.tuple_of_medias        = t_of_medias
        self.tuple_of_sentences     = t_of_sentences

    #Normally this functions shouldn't be here, but I need them to display a progress bar correctly
    def cutMedias(self, vid_filename, tuple_of_medias):
        for media in tuple_of_medias:
            cut(vid_filename, media)

            GLib.idle_add(self.callback)

    def makeCards(self, coll_filename, deck_name, tuple_of_sentences):
        card_type = 'Basic'
        cache_dir = path.abspath('data/cache/media')
        deck = aopen( coll_filename );
        deck_id = deck.decks.id(deck_name)
        deck.decks.select( deck_id )
        model = deck.models.byName( card_type )
        model['did'] = deck_id
        deck.models.save( model )
        deck.models.setCurrent( model )

        for arg in tuple_of_sentences:
            (sentence_front, sentence_back, media)  = arg
            card                                    = deck.newNote()
            fname                                   = deck.media.addFile(cache_dir + '/' + media)
            card['Front']                           = sentence_front + f'[sound:{fname}]'
            card['Back']                            = sentence_back
            deck.addNote( card )
            deck.save()

            GLib.idle_add(self.callback)

        deck.close()

    def run(self):
        clearCachedFiles()
        self.cutMedias(self.vid_filename, self.tuple_of_medias)
        self.makeCards(self.coll_filename, self.deck_name, self.tuple_of_sentences)
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
        self.video_srt_file             = builder.get_object('video_srt_file')
        self.video_srt_file_optional    = builder.get_object('video_srt_file_optional')
        self.deck_name_entry            = builder.get_object('deck_name_entry') 

        try:
            cache_dir       = path.abspath('data/cache')
            cached_usage    = path.join(cache_dir + '/' + 'cached_usage.txt') 
            with open(cached_usage, 'r') as f:
                list_cache = f.read().split('\n')
            self.collection_file.set_filename(list_cache[0])
            self.deck_name_entry.set_text(list_cache[1])
        except:
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

        srt_file_filter = Gtk.FileFilter()
        srt_file_filter.set_name('Srt File')
        srt_file_filter.add_pattern('*.srt')
        self.video_srt_file.add_filter(srt_file_filter)
        self.video_srt_file_optional.add_filter(srt_file_filter)

        GLib.timeout_add(50, self.setSensitiveProceedButton, None)
        
        self.second_window_hided = False
        self.second_window = builder.get_object('second_window')

        self.tuple_of_sentences = ()
        self.tuple_of_medias    = ()

    def setSensitiveProceedButton(self, *args):
        GLib.timeout_add(300, self.setSensitiveProceedButton, None)

        coll_filename           = self.collection_file.get_filename()
        vid_filename            = self.video_file.get_filename()
        vid_srt_filename        = self.video_srt_file.get_filename()
        vid_srt_filename_opt    = self.video_srt_file_optional.get_filename()
        deck_name               = self.deck_name_entry.get_text()

        if all(
              (      checkIfIsCollection(coll_filename),
                     checkIfIsVideo(vid_filename),
                     checkIfIsSrt(vid_srt_filename),
                     checkIfIsSrtOpt(vid_srt_filename_opt)
              )) and checkIfIsSrtOpt(vid_srt_filename_opt) == True and deck_name != '':

            self.button.set_sensitive(True)

        else:
            self.button.set_sensitive(False)

    def on_dellcoll_clicked(self, *args):
       self.collection_file.unselect_all()

    def on_dellvid_clicked(self, *args):
        self.video_file.unselect_all()

    def on_dellsrt_clicked(self, *args):
        self.video_srt_file.unselect_all()

    def on_dellsrtopt_clicked(self, *args):
        self.video_srt_file_optional.unselect_all()

    def on_cancel_process_clicked(self, *args):
        self.second_window_hided = True
        self.second_window.hide()

    def on_proceed_action_clicked(self, *args):
        if not self.second_window_hided:

            self.coll_filename          = self.collection_file.get_filename()
            self.vid_filename           = self.video_file.get_filename()
            self.vid_srt_filename       = self.video_srt_file.get_filename()
            self.vid_srt_filename_opt   = self.video_srt_file_optional.get_filename()
            self.deck_name              = self.deck_name_entry.get_text()

            self.open_srt_file      = openSrtFile(self.vid_srt_filename)
            self.sub_tree_view      = builder.get_object('sub_tree_view')
            self.sub_list_store     = Gtk.ListStore(int, str, str, str, bool, bool)

            if self.vid_srt_filename_opt:
                self.open_srt_file_opt = openSrtFile(self.vid_srt_filename_opt)
                self.sub_list_store_back = Gtk.ListStore(int, str, str, str, bool, bool)
                for i in range(len(self.open_srt_file)):
                    self.sub_list_store_back.append(subExtractReturnTuple(giveMe1Tuple(self.open_srt_file_opt[i])))
            else:
                self.sub_list_store_back = Gtk.ListStore(int, str)
                for i in range(len(self.open_srt_file)):
                    self.sub_list_store_back.append((i, ''))

            for i in range(len(self.open_srt_file)):
                if subExtractReturnTuple(giveMe1Tuple(self.open_srt_file[i])):
                    self.sub_list_store.append(subExtractReturnTuple(giveMe1Tuple(self.open_srt_file[i])))
            
            for i, title in enumerate(['Indice', 'Dialog', 'Start', 'End']):
                renderer = Gtk.CellRendererText()
                path_column = Gtk.TreeViewColumn(title=title, cell_renderer=renderer, text=i)
                path_column.set_sort_column_id(i)
                self.sub_tree_view.append_column(path_column)
                self.sub_tree_view.set_model(self.sub_list_store)

            self.selected_row = self.sub_tree_view.get_selection()
            self.selected_row.connect("changed", self.item_selected)

            # cell video and audio to toggle
            renderer_video_toggle = Gtk.CellRendererToggle()
            column_toggle = Gtk.TreeViewColumn(title='Video', cell_renderer=renderer_video_toggle, active=4)
            self.sub_tree_view.append_column(column_toggle)
            renderer_video_toggle.connect("toggled", self.on_cell_video_toggled)

            renderer_audio_toggle = Gtk.CellRendererToggle()
            column_toggle = Gtk.TreeViewColumn(title='Audio', cell_renderer=renderer_audio_toggle, active=5)
            self.sub_tree_view.append_column(column_toggle)
            renderer_audio_toggle.connect("toggled", self.on_cell_audio_toggled)
        
            self.sub_tree_view.connect('select-all', self.on_select_all_video_toggled)

        writeRecentUsedCached(self.coll_filename, self.deck_name)
        self.second_window.show_all()

    def item_selected(self, selection):
        text_view_front         = builder.get_object('text_view_front')
        model, row              = selection.get_selected()
        text_buffer_front       = text_view_front.get_buffer()

        text_buffer_front.set_text(model[row][1])
        text_buffer_front.connect('changed', self.editing_card)

        text_view_back      = builder.get_object('text_view_back')

        path = self.selected_row.get_selected_rows()[1][0]
        text_buffer_back    = text_view_back.get_buffer()

        text_buffer_back.set_text(self.sub_list_store_back[path][1])
        text_buffer_back.connect('changed', self.editing_card_back)

    def editing_card(self, text_buffer):
        path = self.selected_row.get_selected_rows()[1][0]
        self.sub_list_store[path][1] = text_buffer.get_text(text_buffer.get_start_iter(), text_buffer.get_end_iter(), True)
    
    def editing_card_back(self, text_buffer):
        path = self.selected_row.get_selected_rows()[1][0]
        self.sub_list_store_back[path][1] = text_buffer.get_text(text_buffer.get_start_iter(), text_buffer.get_end_iter(), True)

    def on_cell_video_toggled(self, widget, path):
        if self.sub_list_store[path][5] == True:
            self.sub_list_store[path][5] = not self.sub_list_store[path][5]
            self.sub_list_store[path][4] = not self.sub_list_store[path][4]
        else:
            self.sub_list_store[path][4] = not self.sub_list_store[path][4]

    def on_cell_audio_toggled(self, widget, path):
        if self.sub_list_store[path][4] == True:
            self.sub_list_store[path][4] = not self.sub_list_store[path][4]
            self.sub_list_store[path][5] = not self.sub_list_store[path][5]
        else:
            self.sub_list_store[path][5] = not self.sub_list_store[path][5]

    def on_select_all_video_toggled(self, *args):
        for i in range(len(self.sub_list_store)):
            if self.sub_list_store[i][5] == True:
                self.sub_list_store[i][5] = not self.sub_list_store[i][5]
                self.sub_list_store[i][4] = not self.sub_list_store[i][4]
            else:
                self.sub_list_store[i][4] = not self.sub_list_store[i][4]
    
    def on_select_all_audio_toggled(self, *args):
        for i in range(len(self.sub_list_store)):
            if self.sub_list_store[i][4] == True:
                self.sub_list_store[i][4] = not self.sub_list_store[i][4]
                self.sub_list_store[i][5] = not self.sub_list_store[i][5]
            else:
                self.sub_list_store[i][5] = not self.sub_list_store[i][5]

    #Normally this type of function shouldn't be here, but I need it to display the progress correctly
    def tupleMedias(self, sub_list_store, sub_list_store_back):
        self.tuple_of_sentences = ()
        self.tuple_of_medias    = ()
        for i in range(len(self.sub_list_store)):
            if self.sub_list_store[i][4] == True or self.sub_list_store[i][5] == True:
                self.tuple_of_medias = self.tuple_of_medias + ((tuple(self.sub_list_store[i][:])),)
                if self.sub_list_store[i][4]:
                    self.tuple_of_sentences = self.tuple_of_sentences + ((  self.sub_list_store[i][1],
                                                                            self.sub_list_store_back[i][1],
                                                                            f'{self.sub_list_store[i][0]}.mp4'),)
                else:
                    self.tuple_of_sentences = self.tuple_of_sentences + ((  self.sub_list_store[i][1],
                                                                            self.sub_list_store_back[i][1],
                                                                            f'{self.sub_list_store[i][0]}.mp3'),)

    def on_conclude_process_clicked(self, *args): 
        self.tupleMedias(self.sub_list_store, self.sub_list_store_back)
        thread = MyThread(
                self.update_progress,
                self.sub_list_store,
                self.vid_filename,
                self.sub_list_store_back,
                self.coll_filename,
                self.deck_name,
                self.tuple_of_medias,
                self.tuple_of_sentences)

        thread.start()
    
    def update_progress(self):
        self.current    = self.current + 1
        maximum         = (len(self.tuple_of_medias) + len(self.tuple_of_sentences))
        progress_bar = builder.get_object('progress_bar')
        progress_bar.set_fraction(self.current / maximum)

        if self.current == maximum:
            progress_bar.set_text('Concluded!')
            progress_bar.set_show_text(True)
            self.current = 0
        else:
            progress_bar.set_show_text(False)

        return False

    def on_main_destroy(self, *args):
        Gtk.main_quit()

    def on_cancel_action_clicked(self, *args):
        Gtk.main_quit()


def main():
    builder.connect_signals(Handler())
    window = builder.get_object('main')
    window.show_all()
    Gtk.main()

