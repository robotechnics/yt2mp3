#!/usr/bin/env python3
# yt2mp3.py

import sys, os, youtube_dl, itunespy, cursesmenu, argparse, urllib, requests, ssl, glob, shutil
from pydub import AudioSegment
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TCON
from mutagen.mp3 import MP3
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from pathlib import Path

ydl = youtube_dl.YoutubeDL({
  'format': 'bestaudio/best', # get best audio
  'outtmpl': os.path.join(os.environ['HOME'],'Downloads','YDL', '%(id)s.%(ext)s'), # sets output template
  'nocheckcertificate': True, # bypasses certificate check
  'noplaylist' : True, # won't download playlists
  'quiet': True, #suppress messages in command line
  'postprocessors': [{
      'key': 'FFmpegExtractAudio',
      'preferredcodec': 'mp3',
      'preferredquality': '192',
  }]
})

def main():
  parser = argparse.ArgumentParser(description='YouTube to MP3 Converter')
  parser.add_argument('-u','--url', help='YouTube URL you want to convert')
  args = parser.parse_args()
  # Get song title/artist from user
  # info = {}
  # info['title'] = input('Title: ')
  # info['artist'] = input('Artist: ')
  info = {
    'title': 'Stan',
    'artist': 'Eminem'
  }
  if args.url:
    download(args.url)
    temp_path = glob.glob(str(Path.home()/'Downloads'/'YDL')+'/*.mp3')[0]
    dir = str(Path.home()/'Downloads'/'Music')
    if info['artist']:
      dir = os.path.join(dir, info['artist'])
      os.system('mkdir -p %s' % (dir.replace(' ', '_')))
    # add song to artist directory
    # path = os.path.join(dir, info['title']+'.mp3')
    # os.system('mv %s %s' % (temp_path, path.replace(' ', '_')))
    try:
      song = getTrack(info['title'], info['artist'])
      setData(path, song)
    except Exception as e:
      setID3(path, info)
      pass
  else:
    if info['title']:
      song = getTrack(info['title'], info['artist'])
    elif info['artist']:
      songs = getArtist(info['artist'])
      selection = showMenu(songs)
      song = songs[selection]
      info['title'] = song.track_name
    else:
      print("Sorry, no results were found.")
      sys.exit()
    url = getURL(song.track_name, song.artist_name)
    download(url)
    path = glob.glob(str(Path.home()/'Downloads'/'YDL')+'/*.mp3')[0]
    setData(path, song)
  setPath(path, info['title'], info['artist'])


# Returns a single track object from the itunespy module.
def getTrack(track, artist):
  songs = itunespy.search_track(track)
  for song in songs:
    if song.artist_name.lower() == artist.lower():
      return song

# Returns a list of track objects all made by artist.
def getArtist(artist):
  songs = []
  artists = itunespy.search_artist(artist)[0]
  for album in artists.get_albums():
    for song in album.get_tracks():
      songs.append(song)
  return songs
  
# def getSong(track, artist):
#   if track and artist:
#     songs = itunespy.search_track(track)
#     for song in songs:
#       if song.artist_name.lower() == artist.lower():
#         return song
#   elif artist:
#     songs = []
#     artists = itunespy.search_artist(artist)[0]
#     for album in artists.get_albums():
#       for song in album.get_tracks():
#         songs.append(song)
#     return songs

# Displays an interactive menu of songs
def showMenu(songs):
  options = [str(s.track_name) for s in songs]
  menu = cursesmenu.SelectionMenu(options, title='Select an song')
  selection = menu.get_selection(options)
  return selection
  
# Scrapes youtube for a video that has track and artist in the name
def getURL(track, artist):
  query = urllib.parse.quote(track+" "+artist)
  url = "https://www.youtube.com/results?search_query=" + query
  req = Request(url, headers={'User-Agent':'Mozilla/5.0'})
  resp = urlopen(req, context=ssl._create_unverified_context())
  soup = BeautifulSoup(resp.read(), 'lxml')
  search_results = []
  for vid in soup.findAll(attrs={'class':'yt-uix-tile-link'}):
    search_results.append('https://www.youtube.com' + vid['href'])
  return search_results[0]

# Downloads songs from youtube, songs must be a list of track objects
def download(url):
  if len(url) <= 15:
    url = 'https://www.youtube.com/watch?v='+url
  ydl.download([url])

# Sets the ID3 meta data of the MP3 file found at the end of path
def setData(path, song):
  new_song = ID3(path)
  new_song.delete()
  new_song.add(TIT2(encoding=3, text=song.track_name))
  new_song.add(TPE1(encoding=3, text=song.artist_name))
  new_song.add(TALB(encoding=3, text=song.collection_name))
  new_song.add(TCON(encoding=3, text=song.primary_genre_name))
  new_song.save()
  # Embed cover-art in ID3 metadata
  new_song = MP3(path, ID3=ID3)
  img_url = song.artwork_url_100
  dir = str(Path.home()/'Downloads'/'CoverArt')
  os.system('mkdir -p %s' % (dir))
  img_path = os.path.join(dir,song.collection_name+'.jpg')
  img_response = requests.get(img_url)
  img = Image.open(BytesIO(img_response.content))
  img.save(img_path)
  new_song.tags.add(APIC(encoding=3, mime="image/jpg",
                        type=3, desc=u"Cover",
                        data=open(img_path, "rb").read()))
  new_song.save()
  shutil.rmtree(dir)

# Sets the file path of song to: Music/[artist]/[track].mp3
def setPath(path, track, artist):
  # make artist directory
  dir = str(Path.home()/'Downloads'/'Music'/artist)
  os.system('mkdir -p %s' % (dir.replace(' ', '_')))
  # add song to artist directory
  new_path = os.path.join(dir,track+'.mp3')
  os.system('mv %s %s' % (path, new_path.replace(' ', '_')))
  shutil.rmtree(Path.home()/'Downloads'/'YDL')
  
# Set MP3 ID3 tags
def setID3(path, info):
  song = EasyID3(path)
  song['title'] = info['title']
  song['artist'] = info['artist']
  song.save()  


if __name__ == '__main__':
  main()