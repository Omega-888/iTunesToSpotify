import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import csv

# CONFIG
CLIENT_ID = 'your_client_id_here'  # Inserisci il tuo Client ID
# Puoi ottenerlo da https://developer.spotify.com/dashboard/applications
CLIENT_SECRET = 'your_client_secret_here'  # Inserisci il tuo Client Secret
REDIRECT_URI = 'http://127.0.0.1:8888/callback/'  # usa 127 invece di localhost
SCOPE = 'playlist-modify-private playlist-modify-public'

# Autenticazione Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope=SCOPE,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI
))

# Legge le tracce dal file TXT esportato da iTunes
def read_tracks_from_txt(file_path):
    tracks = []
    with open(file_path, newline='', encoding='utf-16') as txtfile:
        reader = csv.DictReader(txtfile, delimiter='\t')
        for row in reader:
            # Normalizza tutte le chiavi rimuovendo eventuali BOM
            normalized_row = {k.lstrip('\ufeff'): v for k, v in row.items()}
            name = normalized_row.get('Nome') or normalized_row.get('Titolo') or normalized_row.get('Name')
            artist = normalized_row.get('Artista') or normalized_row.get('Artist')
            if name and artist:
                name = name.strip()
                artist = artist.strip()
                tracks.append((name, artist))
    return tracks

# Cerca traccia su Spotify
def search_song(name, artist):
    query = f"track:{name} artist:{artist}"
    result = sp.search(q=query, type='track', limit=1)
    items = result['tracks']['items']
    return items[0]['uri'] if items else None

# Crea playlist privata e aggiunge i brani
def create_playlist_and_add_tracks(tracks):
    user_id = sp.me()['id']
    playlist = sp.user_playlist_create(user_id, 'Playlist Importata da iTunes', public=False)
    uris = []
    not_found = []

    for name, artist in tracks:
        uri = search_song(name, artist)
        if uri:
            print(f"✔️  Trovato: {name} - {artist}")
            uris.append(uri)
        else:
            print(f"❌ NON trovato: {name} - {artist}")
            not_found.append(f"{name} - {artist}")
        time.sleep(0.1)

    print(f"\n🎧 Trovate {len(uris)} tracce su {len(tracks)} totali.")

    for i in range(0, len(uris), 100):
        sp.playlist_add_items(playlist['id'], uris[i:i+100])

    if not_found:
        with open('non_trovati.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(not_found))
        print(f"📄 Brani non trovati salvati in 'non_trovati.txt'.")

    print(f"✅ Playlist creata (privata): {playlist['external_urls']['spotify']}")

# ESECUZIONE
if __name__ == '__main__':
    file_path = 'playlist.txt'
    tracks = read_tracks_from_txt(file_path)
    print(f"📂 Letti {len(tracks)} brani dalla playlist esportata.")
    if tracks:
        print(f"🎵 Prime 5 tracce: {tracks[:5]}")
        create_playlist_and_add_tracks(tracks)
    else:
        print("⚠️ Nessuna traccia trovata nel file. Controlla intestazioni e formato.")