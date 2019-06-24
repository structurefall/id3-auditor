#!/usr/local/bin/python3

# Eric's script to fix mismatched directory names for MP3/M4A music libraries.
# Eric Gottesman, 2019.
# eric@everythinggoescold.com
#
# This doesn't work yet and has no error checking, don't use it. I'll make a
# proper rights comment when it's ready.

import mutagen
import re
import json
from os import scandir
from os import environ

basedir = environ['HOME'] + '/Music/iTunes/iTunes Media/'
skiplist_file = environ['PWD'] + '/skiplist.json'
dotfile_re = re.compile('^\..*')
mp3_re = re.compile('.*\.mp3$')
m4a_re = re.compile('.*\.m4a$')

# Get a list of artist directories, skipping any in the skiplist file
def get_directory_artists():
    all_items = list()
    skiplist = json.load(open(skiplist_file, 'r'))
    for item in scandir(path=basedir):
        if item.is_dir() and not dotfile_re.match(item.name) and item.name not in skiplist:
            all_items.append(item.name)
    print(all_items)
    return all_items

# Get a list of album directories for a given artist directory
def get_albums_per_artist(artist):
    directory = basedir + '/' + artist
    all_albums = list()
    for item in scandir(path=directory):
        if item.is_dir() and not dotfile_re.match(item.name):
            all_albums.append(item.name)
    return all_albums

# Check the ID3 artist name on the first track of a given album and artist directory
def get_artist_name_from_first_track(artist, album):
    directory = basedir + '/' + artist + '/' + album
    all_files = list()
    for item in scandir(path=directory):
        if item.is_file() and (mp3_re.match(item.name) or m4a_re.match(item.name)):
            all_files.append(item.name)
    first_song = all_files[0]
    handler = mutagen.File(directory + '/' + first_song)
    track_artist = str()
    if m4a_re.match(first_song):
        track_artist = handler['©ART'][0]
    elif mp3_re.match(first_song):
        track_artist = handler['TPE1'].text[0]
    return track_artist

# For albums we already know have discrepancies, check to see if there are different
# artist ID3 tags on different tracks. We should already be skipping compilations via
# the skiplist- this is for albums that have one track with "So-and-so feat. So-and-so"
def check_for_multi_artist_album(artist, album):
    directory = basedir + '/' + artist + '/' + album
    all_files = list()
    artist_list = list()
    for item in scandir(path=directory):
        if item.is_file() and (mp3_re.match(item.name) or m4a_re.match(item.name)):
            all_files.append(item.name)
    for file in all_files:
        handler = mutagen.File(directory + '/' + file)
        track_artist = str()
        if m4a_re.match(file):
            track_artist = handler['©ART'][0]
        elif mp3_re.match(file):
            track_artist = handler['TPE1'].text[0]
        if track_artist not in artist_list:
            artist_list.append(track_artist)
    if len(artist_list) > 1:
        return artist_list
    else:
        return None

# Once we know about albums with discrepancies, use the list of discrepancies to
# start processing.
def process_discrepancies(discrepancies_list):
    for issue in discrepancies_list:
        multi = check_for_multi_artist_album(issue['dir_artist'],issue['album'])
        print("For the album \"{}\", choose:".format(issue['album']))
        print(" [0] {} (Directory artist)".format(issue['dir_artist']))
        artist_options = list()
        if multi == None:
            artist_options.append(issue['track_artist'])
        else:
            artist_options = multi
        num = 1
        for artist in artist_options:
            print(" [{}] {}".format(num,artist))
            num += 1
        print(' [ <Some other thing> ] <Some other thing>')
        print(' [] Leave it as-is')
        selection = input('> ')
        if len(selection) > 0:
            if selection == "0":
                print("asdggsd")
                final_artist = issue['dir_artist']
            else:
                try:
                    final_artist = artist_options[int(selection)-1]
                except ValueError:
                    final_artist = selection
                except IndexError:
                    print("Invalid selection, skipping.")
                    final_artist = None
        if final_artist != None:
            print("Selecting {}.".format(final_artist))
        return final_artist




def main():
    directory_artists = get_directory_artists()

    discrepancies = list()
    failures = list()
    for dir_artist in get_directory_artists():
        print("Processing {}...".format(dir_artist))
        for album in get_albums_per_artist(dir_artist):
            print(" - {}".format(album))
            try:
                track_artist = get_artist_name_from_first_track(dir_artist, album)
                if track_artist != dir_artist:
                    discrepancies.append(
                        {
                            "dir_artist": dir_artist,
                            "track_artist": track_artist,
                            "album": album
                        }
                    )
            except Exception as message:
                print("Failed on {}/{}: {}".format(dir_artist, album, message))
                failures.append(
                    {
                        "dir_artist": dir_artist,
                        "album": album
                    }
                )
    print("\n\nDiscrepancies: {}".format(discrepancies))
    process_discrepancies(discrepancies)
    print("\nFailures: {}".format(failures))




main()
