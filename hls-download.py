# written wiht python3.7

# https://s3.amazonaws.com/hls-demos/nokia/index.m3u8

import sys
import re
from pathlib import Path
import os.path
import urllib.request
from urllib.parse import urlparse
from urllib.parse import urljoin
import m3u8

if len(sys.argv) < 3:
	print("Not enough arguments. Please use hls-download.py <hls url> <output dir>");
	sys.exit()

master_playlist_url = sys.argv[1]

# TODO check and add m3u8 check at the end of url
regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
if re.match(regex, master_playlist_url) is None:
	print("Invalid url. Please check that hls playlist is a valid http url")
	sys.exit()

def savePlaylistToFile(playlist, path):
	path.parent.mkdir(parents=True, exist_ok=True)
	path = open(path, 'w')
	path.write(playlist)
	path.close()

def downloadSegments(media_playlist_str, base_url, dir_path):
	media_m3u8_obj = m3u8.loads(media_playlist_str)
	segments = media_m3u8_obj.segments.by_key(media_m3u8_obj.keys[-1])
	for segment_index, segment in enumerate(segments):
		segment_url = urljoin(base_url, segment.uri)
		segment_path = dir_path.joinpath(segment.uri)
		segment_path.parent.mkdir(parents=True, exist_ok=True)
		print('Downloading {0}/{1} segment: {2} to {3}'.format(
			segment_index + 1,
			len(segments),
			segment_url,
			segment_path));
		urllib.request.urlretrieve(segment_url, segment_path)


master_playlist_path = Path(sys.argv[2]).joinpath(os.path.basename(urlparse(master_playlist_url).path))
print('Downloading master playlist: {0} to {1}'.format(master_playlist_url, master_playlist_path))

master_playlist = urllib.request.urlopen(master_playlist_url).read().decode('utf-8')
savePlaylistToFile(master_playlist, master_playlist_path)

master_m3u8_obj = m3u8.loads(master_playlist)

for playlist_index, playlist in enumerate(master_m3u8_obj.playlists):	
	media_playlist_url = urljoin(master_playlist_url, playlist.uri)
	media_playlist_path = master_playlist_path.parent.joinpath(playlist.uri);
	
	print('Downloading {0}/{1} media playlist: {2} to {3}'.format(
			playlist_index + 1, 
			len(master_m3u8_obj.playlists), 
			media_playlist_url, 
			media_playlist_path))

	media_playlist = urllib.request.urlopen(media_playlist_url).read().decode('utf-8')
	savePlaylistToFile(media_playlist, media_playlist_path)

	downloadSegments(media_playlist, media_playlist_url, media_playlist_path.parent)
