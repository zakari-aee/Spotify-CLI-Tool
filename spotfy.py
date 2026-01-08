import requests
import base64
import re
import os
from typing import Optional, Dict, List
from urllib.parse import urlparse, parse_qs

class SpotifyAPI:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.authenticate()

    def authenticate(self):
        """Get access token from Spotify"""
        auth_url = "https://accounts.spotify.com/api/token"
        # Encode credentials
        credentials = f"{self.client_id}:{self.client_secret}"
        credentials_b64 = base64.b64encode(credentials.encode()).decode()
        headers = {
            "Authorization": f"Basic {credentials_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        try:
            response = requests.post(auth_url, headers=headers, data=data)
            response.raise_for_status()
            self.access_token = response.json()["access_token"]
            print("✓ Authentication successful!")
        except requests.exceptions.RequestException as e:
            print(f"✗ Authentication failed: {e}")
            raise

    def extract_id_from_url(self, url: str) -> Optional[tuple]:
        """Extract Spotify ID and type from URL
        Returns: (id, type) where type is 'track', 'album', 'playlist', etc.
        """
        pattern = r'https://open\.spotify\.com/([a-z]+)/([a-zA-Z0-9?=&]+)'
        match = re.search(pattern, url)
        if match:
            spotify_type = match.group(1)
            spotify_id = match.group(2)
            # Remove query parameters if present
            spotify_id = spotify_id.split('?')[0]
            return spotify_id, spotify_type
        return None

    def search_track(self, track_name: str, limit: int = 5) -> List[Dict]:
        if not self.access_token:
            print("Not authenticated")
            return []
        url = "https://api.spotify.com/v1/search"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {
            "q": track_name,
            "type": "track",
            "limit": limit
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            tracks = response.json()["tracks"]["items"]
            return tracks
        except requests.exceptions.RequestException as e:
            print(f"✗ Search failed: {e}")
            return []

    def get_track_by_id(self, track_id: str) -> Optional[Dict]:
        if not self.access_token:
            print("Not authenticated")
            return None
        url = f"https://api.spotify.com/v1/tracks/{track_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to get track: {e}")
            return None

    def get_album(self, album_id: str) -> Optional[Dict]:
        """Get album information by ID"""
        if not self.access_token:
            print("Not authenticated")
            return None
        url = f"https://api.spotify.com/v1/albums/{album_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to get album: {e}")
            return None

    def get_album_tracks(self, album_id: str) -> List[Dict]:
        if not self.access_token:
            print("Not authenticated")
            return []
        url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        tracks = []
        try:
            while url:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                tracks.extend(data.get("items", []))
                url = data.get("next")
            return tracks
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to get album tracks: {e}")
            return []

    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        if not self.access_token:
            print("Not authenticated")
            return []
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        tracks = []
        try:
            while url:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                tracks.extend(data.get("items", []))
                url = data.get("next")
            print(f"✓ Retrieved {len(tracks)} tracks from playlist")
            return tracks
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to get playlist: {e}")
            return []

    def get_track_features(self, track_id: str) -> Optional[Dict]:
        if not self.access_token:
            print("Not authenticated")
            return None
        url = f"https://api.spotify.com/v1/audio-features/{track_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠ Audio features not available: {e}")
            return None

    def display_track_info(self, track: Dict):
        artists = ", ".join([artist["name"] for artist in track.get("artists", [])])
        spotify_url = track.get('external_urls', {}).get('spotify', 'N/A')
        print(f"\n🎵 {track['name']}")
        print(f" Artist: {artists}")
        print(f" Album: {track['album']['name']}")
        print(f" Duration: {track['duration_ms'] // 60000}:{(track['duration_ms'] % 60000) // 1000:02d}")
        print(f" Popularity: {track.get('popularity', 'N/A')}/100")
        print(f" ID: {track['id']}")
        print(f" 🔗 URL: {spotify_url}")

    def display_album_info(self, album: Dict):
        artists = ", ".join([artist["name"] for artist in album.get("artists", [])])
        spotify_url = album.get('external_urls', {}).get('spotify', 'N/A')
        print(f"\n💿 {album['name']}")
        print(f" Artist: {artists}")
        print(f" Release Date: {album.get('release_date', 'N/A')}")
        print(f" Total Tracks: {album.get('total_tracks', 'N/A')}")
        print(f" ID: {album['id']}")
        print(f" 🔗 URL: {spotify_url}")

    def save_tracks_to_file(self, tracks: List[Dict], filename: str = "spotify_tracks.txt"):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("SPOTIFY TRACKS\n")
                f.write("="*80 + "\n\n")
                for i, track in enumerate(tracks, 1):
                    artists = ", ".join([artist["name"] for artist in track.get("artists", [])])
                    url = track.get('external_urls', {}).get('spotify', 'N/A')
                    f.write(f"{i}. {track['name']}\n")
                    f.write(f" Artist: {artists}\n")
                    f.write(f" Album: {track['album']['name']}\n")
                    f.write(f" URL: {url}\n")
                    f.write(f" ID: {track['id']}\n")
                    f.write("\n")
            print(f"\n✓ Saved {len(tracks)} tracks to '{filename}'")
            return True
        except Exception as e:
            print(f"✗ Failed to save file: {e}")
            return False

# ===== INTERACTIVE SCRIPT =====
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎵 SPOTIFY SEARCH TOOL")
    print("="*60)
    print("\n📝 Enter your Spotify API credentials:")
    print("(Get them from: https://developer.spotify.com/dashboard)\n")
    
    CLIENT_ID = input("🔑 SPOTIFY_CLIENT_ID: ").strip()
    CLIENT_SECRET = input("🔑 SPOTIFY_CLIENT_SECRET: ").strip()
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("\n❌ Error: Both Client ID and Client Secret are required!")
        exit()
    
    # Initialize the API
    try:
        spotify = SpotifyAPI(CLIENT_ID, CLIENT_SECRET)
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        exit()
    
    print("\n" + "="*60)
    print("🎵 SPOTIFY SEARCH TOOL")
    print("="*60)
    print("\nYou can search by:")
    print("1. Spotify URL (e.g., https://open.spotify.com/track/...)")
    print("2. Track name (e.g., 'Blinding Lights')")
    print("\n(Press Ctrl+C to exit)\n")

    while True:
        try:
            user_input = input("Enter Spotify URL or track name: ").strip()
            if not user_input:
                print("Please enter something!")
                continue

            # Check if it's a URL
            if user_input.startswith("http"):
                print("\n🔍 Parsing URL...")
                result = spotify.extract_id_from_url(user_input)
                if not result:
                    print("❌ Invalid Spotify URL format")
                    continue
                spotify_id, spotify_type = result
                print(f"✓ Found {spotify_type.upper()} ID: {spotify_id}")

                # Handle different types
                if spotify_type == "track":
                    print("\n" + "="*60)
                    print("TRACK INFORMATION")
                    print("="*60)
                    track = spotify.get_track_by_id(spotify_id)
                    if track:
                        spotify.display_track_info(track)
                        # Try to get audio features
                        features = spotify.get_track_features(spotify_id)
                        if features:
                            print(f"\n📊 Audio Features:")
                            print(f" Tempo (BPM): {features['tempo']}")
                            print(f" Energy: {features['energy']:.2f}/1.0")
                            print(f" Danceability: {features['danceability']:.2f}/1.0")
                        # Save option
                        save = input("\nSave to file? (y/n): ").lower()
                        if save == 'y':
                            spotify.save_tracks_to_file([track], "track.txt")

                elif spotify_type == "album":
                    print("\n" + "="*60)
                    print("ALBUM INFORMATION")
                    print("="*60)
                    album = spotify.get_album(spotify_id)
                    if album:
                        spotify.display_album_info(album)
                        # Get album tracks
                        tracks = spotify.get_album_tracks(spotify_id)
                        if tracks:
                            print(f"\n📋 Tracks ({len(tracks)} total):")
                            for i, track in enumerate(tracks[:10], 1):
                                duration = f"{track['duration_ms'] // 60000}:{(track['duration_ms'] % 60000) // 1000:02d}"
                                print(f" {i}. {track['name']} ({duration})")
                            if len(tracks) > 10:
                                print(f" ... and {len(tracks) - 10} more tracks")
                        # Save option
                        save = input("\nSave all tracks to file? (y/n): ").lower()
                        if save == 'y':
                            filename = f"album_{album['name']}.txt"
                            spotify.save_tracks_to_file(tracks, filename)

                elif spotify_type == "playlist":
                    print("\n" + "="*60)
                    print("PLAYLIST TRACKS")
                    print("="*60)
                    tracks = spotify.get_playlist_tracks(spotify_id)
                    if tracks:
                        print(f"📋 Tracks ({len(tracks)} total):")
                        for i, item in enumerate(tracks[:10], 1):
                            track = item.get("track")
                            if track:
                                artist = track['artists'][0]['name'] if track['artists'] else "Unknown"
                                duration = f"{track['duration_ms'] // 60000}:{(track['duration_ms'] % 60000) // 1000:02d}"
                                print(f" {i}. {track['name']} - {artist} ({duration})")
                        if len(tracks) > 10:
                            print(f" ... and {len(tracks) - 10} more tracks")
                        # Save option
                        save = input("\nSave all tracks to file? (y/n): ").lower()
                        if save == 'y':
                            playlist_tracks = [item['track'] for item in tracks if item.get('track')]
                            spotify.save_tracks_to_file(playlist_tracks, "playlist_tracks.txt")

                else:
                    print(f"❌ Unsupported type: {spotify_type}")

            else:
                # Search by track name
                print(f"\n🔍 Searching for: '{user_input}'...")
                tracks = spotify.search_track(user_input, limit=5)
                if not tracks:
                    print("❌ No tracks found")
                    continue
                print("\n" + "="*60)
                print("SEARCH RESULTS")
                print("="*60)
                for i, track in enumerate(tracks, 1):
                    spotify.display_track_info(track)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")