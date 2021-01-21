from os                 import environ, mkdir, path, remove, sys, system
from glob               import glob
from anki               import Collection as aopen

from gi                 import require_version
require_version('Gtk', '3.0')
from gi.repository      import GLib
from gi.repository.Gtk  import TextBuffer

sys.path.append(path.abspath('pylib/pyasstosrt'))
sys.path.append(path.abspath('pylib/pysrt'))
from pysrt              import open as popen
from pyasstosrt         import Subtitle

def createCacheDirIfItNotExists():
    if not path.exists(path.abspath('data')):
        mkdir('data')
    if not path.exists(path.abspath('data/cache')):
        mkdir('data/cache')
    if not path.exists(path.abspath('data/cache/media')):
        mkdir('data/cache/media')

def writeRecentUsedCached(anki_collection_filename_path, deck_name):
    cache_dir = path.abspath('data/cache')
    data = f'{anki_collection_filename_path}\n{deck_name}'

    with open(cache_dir + '/' + 'cached_usage.txt', 'w+') as f:
        f.write(data)
        f.close()

def clearCachedFiles():
    try:
        cache_dir       = path.abspath('data/cache')
        cache_media_dir = path.join(cache_dir + '/' + 'media' + '/')
        files = glob(cache_media_dir + '/' + '*')
        for file in files:
            remove(file)
    except:
        pass

def makeCards(anki_collection, deck_name, tuple_of_sentences):
    card_type = 'Basic'
    cache_dir = path.abspath('data/cache/media')
    deck = aopen( anki_collection );
    deck_id = deck.decks.id(deck_name)
    deck.decks.select( deck_id )
    model = deck.models.byName( card_type )
    model['did'] = deck_id
    deck.models.save( model )
    deck.models.setCurrent( model )

    for arg in tuple_of_sentences:
        (sentence_front, sentence_back, media) = arg
        card            = deck.newNote()
        fname = deck.media.addFile(cache_dir + '/' + media)
        card['Front']   = sentence_front + f'[sound:{fname}]'
        card['Back']    = sentence_back
        deck.addNote( card )
        deck.save()

    deck.close()

def cut(input_file, tuple_of_filenames, lock, callback):
    with lock:
        cache_dir   = path.abspath('data/cache/media')
        output_file = cache_dir + '/' + str(tuple_of_filenames[0])
        start       = tuple_of_filenames[2]
        end         = tuple_of_filenames[3]
        video       = tuple_of_filenames[4]
        audio       = tuple_of_filenames[5]
        snapshot    = tuple_of_filenames[6]

        if video:
            cmd = f"ffmpeg -v quiet -y -i '{input_file}' -ss {start} -to {end} -vf scale=640:-1 -async 1 {output_file}.mp4"
            system(cmd)
        if audio:
            cmd = f"ffmpeg -v quiet -y -i '{input_file}' -vn -ss {start} -to {end} -b:a 320k {output_file}.mp3"
            system(cmd)
        if snapshot:
            cmd = f"ffmpeg -v quiet -y -ss {start} -i '{input_file}' -vsync 0 -vframes 1 -filter:v scale=640:-1 {output_file}.bmp"
            system(cmd)

        GLib.idle_add(callback)

def checkIfIsCollection(collection_filename=None):
    if collection_filename == None:
        collection_filename = ''
    if 'anki2' in collection_filename.split('.')[-1]:
        return True
    return False

def checkIfIsVideo(video_filename=None):
    if video_filename == None:
        video_filename = ''
    if video_filename.split('.')[-1] in ('mp4', 'wmv', 'avi', 'mkv', 'webm'):
        return True
    return False

def checkIfIsAss(sub_filename=None):
    if sub_filename == None:
        sub_filename = ''
    if 'ass' in sub_filename.split('.')[-1]:
        return True
    return False

def checkIfIsSrt(sub_filename=None):
    if sub_filename == None:
        sub_filename = ''
    if 'srt' in sub_filename.split('.')[-1]:
        return True
    return False

def checkIfIsSub(sub_filename=None):
    if checkIfIsSrt(sub_filename) == True or checkIfIsAss(sub_filename) == True:
        return True
    return False

def checkIfIsSubOpt(sub_filename_optional=None):
    if sub_filename_optional == None:
        sub_filename_optional = '' 
    if checkIfIsSub(sub_filename_optional) == True or sub_filename_optional == '':
        return True
    return False

def openSubFile(f_path):
    if checkIfIsAss(f_path):
        return Subtitle(f_path).export()
    return popen(f_path)

def giveMe1Tuple(opened_sub_indexed):
    return tuple(str(opened_sub_indexed).split('\n'))

def subExtractReturnTuple(opened_sub_tupled):
    tuple_sub = (opened_sub_tupled[:2]) + (''.join(opened_sub_tupled[2:]),)

    if len(tuple_sub[2]) > 3:  
        final_tuple =   (int(tuple_sub[0]),) + \
                        ((tuple_sub[2]),) + \
                        ((tuple_sub[1].split('-->')[0].replace(',','.')),) + \
                        ((tuple_sub[1].split('-->')[1].replace(',','.')),) + \
                        (False,) + (False,) + (False,)

        return final_tuple

    return ()

def serializeIt(text_buffer, tmp_string=None):
    if tmp_string:
        text_buffer.set_text(tmp_string)
        tmp_start_iter  = text_buffer.get_start_iter()
        tmp_end_iter    = text_buffer.get_end_iter()
        tmp_format      = text_buffer.register_serialize_tagset()
        tmp_exported    = text_buffer.serialize( text_buffer,
                                                 tmp_format,
                                                 tmp_start_iter,
                                                 tmp_end_iter )
        return tmp_exported
    else:
        start_iter  = text_buffer.get_start_iter()
        end_iter    = text_buffer.get_end_iter()
        format      = text_buffer.register_serialize_tagset()
        exported    = text_buffer.serialize( text_buffer,
                                             format,
                                             start_iter,
                                             end_iter )
        return exported

def deserializeIt(text_buffer, exported):
    text_buffer.set_text('')
    text_buffer.deserialize(text_buffer,
                            text_buffer.register_deserialize_tagset(),
                            text_buffer.get_start_iter(),
                            exported )

