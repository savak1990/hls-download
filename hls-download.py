#!/usr/bin/env python3.7

# 3.7 python is used

import sys
import re
from pathlib import Path
import os.path
import urllib.request
from urllib.parse import urlparse
from urllib.parse import urljoin
import m3u8

# Validation of the args
if len(sys.argv) < 3:
	print("Not enough arguments. Please use hls-download.py <hls url> <output dir>");
	sys.exit()

master_playlist_url = sys.argv[1]

# Validation of the url
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


def downloadSegment(url, path, index, total, playlist_index, playlist_total):
	print('Playlist {0}/{1}: Downloading {2}/{3} segment: {4} to {5}'.format(
			playlist_index, playlist_total, index, total, url, path));
	urllib.request.urlretrieve(url, path)


def downloadSegments(media_playlist_str, base_url, dir_path, playlist_index, playlist_total):
	media_m3u8_obj = m3u8.loads(media_playlist_str)
	segments = media_m3u8_obj.segments.by_key(media_m3u8_obj.keys[-1])
	for segment_index, segment in enumerate(segments):
		segment_url = urljoin(base_url, segment.uri)
		segment_path = dir_path.joinpath(segment.uri)
		segment_path.parent.mkdir(parents=True, exist_ok=True)
		downloadSegment(segment_url, 
						segment_path, 
						segment_index + 1, 
						len(segments), 
						playlist_index, 
						playlist_total)
		

def downloadMediaPlaylist(url, path, index, total, playlist_name):
	print('Downloading {0}/{1} {2}: {3} to {4}'.format(
			index, total, playlist_name, url, path))
	return urllib.request.urlopen(url).read().decode('utf-8')

def downloadMediaPlaylists(master_playlist_str, base_url, dir_path):
	master_m3u8_obj = m3u8.loads(master_playlist_str)

	# m3u8 doesn't work with audio streams. So retrive it's uri by simple regex
	#TODO figure out more accurate way of getting audio streams
	audio_playlists = []
	for line in master_playlist_str.splitlines():
		if 'TYPE=AUDIO' in line:
			match = re.search(r'URI="(.*?)"', line)
			if match:
				audio_playlists.append(match.group(1))


	print('Media playlists: {0} iFrame playlists: {1} Audio playlists: {2}'.format( 
			len(master_m3u8_obj.playlists), 
			len(master_m3u8_obj.iframe_playlists),
			len(audio_playlists)))


	# Loop over all media playlists
	for index, playlist in enumerate(master_m3u8_obj.playlists):
		media_playlist_url = urljoin(base_url, playlist.uri)
		media_playlist_path = dir_path.joinpath(playlist.uri);

		media_playlist = downloadMediaPlaylist(
				media_playlist_url, 
				media_playlist_path, 
				index + 1, 
				len(master_m3u8_obj.playlists),
				"media playlist")
		savePlaylistToFile(media_playlist, media_playlist_path)

		downloadSegments(media_playlist, 
						 media_playlist_url, 
						 media_playlist_path.parent,
						 index + 1,
						 len(master_m3u8_obj.playlists))


	# Loop over all audio playlists
	for index, playlist_uri_str in enumerate(audio_playlists):
		audio_playlist_url = urljoin(base_url, playlist_uri_str)
		audio_playlist_path = dir_path.joinpath(playlist_uri_str)	
		audio_playlist = downloadMediaPlaylist(
				audio_playlist_url,
				audio_playlist_path,
				index + 1,
				len(audio_playlists),
				"audio playlist")
		savePlaylistToFile(audio_playlist, audio_playlist_path)

		downloadSegments(audio_playlist,
						 audio_playlist_url,
						 audio_playlist_path.parent,
						 index + 1,
						 len(audio_playlists))


	# Loop over all i-frame playlists
	for index, playlist in enumerate(master_m3u8_obj.iframe_playlists):
		iframe_playlist_url = urljoin(base_url, playlist.uri)
		iframe_playlist_path = dir_path.joinpath(playlist.uri)

		iframe_playlist = downloadMediaPlaylist(
				iframe_playlist_url,
				iframe_playlist_path, 
				index + 1, 
				len(master_m3u8_obj.iframe_playlists),
				"iframe playlist")
		savePlaylistToFile(iframe_playlist, iframe_playlist_path)

		downloadSegments(iframe_playlist,
						 iframe_playlist_url,
						 iframe_playlist_path.parent,
						 index + 1,
						 len(master_m3u8_obj.iframe_playlists))



def downloadMasterPlaylist(url, path):
	print('Downloading master playlist: {0} to {1}'.format(url, path))
	return urllib.request.urlopen(url).read().decode('utf-8')

#----------------------------------------------------------------
#----------------------------------------------------------------
#----------------------------------------------------------------

master_playlist_path = Path(sys.argv[2]).joinpath(os.path.basename(urlparse(master_playlist_url).path))
master_playlist = downloadMasterPlaylist(master_playlist_url, master_playlist_path)
savePlaylistToFile(master_playlist, master_playlist_path)

downloadMediaPlaylists(master_playlist, master_playlist_url, master_playlist_path.parent)
