import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import csv
import pandas as pd

# CONFIG
CLIENT_ID = 'your_client_id_here' # Inserisci il tuo Client ID di Spotify
CLIENT_SECRET = 'your_client_secret_here' # Inserisci il tuo Client Secret di Spotify
REDIRECT_URI = 'http://127.0.0.1:8888/callback/'  # usa 127 invece di localhost
SCOPE = 'playlist-modify-private playlist-modify-public'

# Autenticazione Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope=SCOPE,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    show_dialog=True
))

# Legge le tracce dal file TXT esportato da iTunes
def read_tracks_from_txt(file_path):
    tracks = []
    with open(file_path, newline='', encoding='utf-16') as txtfile:
        reader = csv.DictReader(txtfile, delimiter='\t')
        for row in reader:
            normalized_row = {k.lstrip('\ufeff'): v for k, v in row.items()}
            name = normalized_row.get('Nome') or normalized_row.get('Titolo') or normalized_row.get('Name')
            artist = normalized_row.get('Artista') or normalized_row.get('Artist')
            album = normalized_row.get('Album') or normalized_row.get('Album')
            if name and artist:
                name = name.strip()
                artist = artist.strip()
                album = album.strip() if album else ''
                tracks.append((name, artist, album))
    return tracks

# Cerca traccia su Spotify (match su nome, artista e album se disponibile)
def search_song(name, artist, album):
    # Prima prova: titolo + artista + album
    query = f"track:{name} artist:{artist}"
    if album:
        query += f" album:{album}"
    result = sp.search(q=query, type='track', limit=3)
    items = result['tracks']['items']
    if items:
        return items[0]['uri'], items

    # Seconda prova: solo titolo + artista
    query = f"track:{name} artist:{artist}"
    result = sp.search(q=query, type='track', limit=3)
    items = result['tracks']['items']
    if items:
        return items[0]['uri'], items

    # Terza prova: solo titolo
    query = f"track:{name}"
    result = sp.search(q=query, type='track', limit=3)
    items = result['tracks']['items']
    if items:
        return items[0]['uri'], items

    return None, []

# Crea playlist e aggiunge i brani trovati
def create_playlist_and_add_tracks(tracks):
    user_id = sp.me()['id']
    playlist = sp.user_playlist_create(user_id, 'Playlist Importata da iTunes', public=False)
    uris = []
    not_found = []
    log_data = []

    for name, artist, album in tracks:
        uri, candidates = search_song(name, artist, album)
        if uri:
            print(f"✔️  Trovato: {name} - {artist} [{album}]")
            uris.append(uri)
            top_matches = ", ".join([f"{t['name']} - {t['artists'][0]['name']}" for t in candidates])
            log_data.append({
                'Titolo': name,
                'Artista': artist,
                'Album': album,
                'Spotify URI': uri,
                'Possibili Alternative': top_matches
            })
        else:
            print(f"❌ NON trovato: {name} - {artist} [{album}]")
            not_found.append({'Titolo': name, 'Artista': artist, 'Album': album})
        time.sleep(0.1)

    print(f"\n🎧 Trovate {len(uris)} tracce su {len(tracks)} totali.")

    for i in range(0, len(uris), 100):
        sp.playlist_add_items(playlist['id'], uris[i:i+100])

    # Salva log CSV con tracce trovate
    df_found = pd.DataFrame(log_data)
    df_found.to_csv('tracce_trovate.csv', index=False, encoding='utf-8')

    # Salva log CSV con tracce non trovate
    if not_found:
        df_missing = pd.DataFrame(not_found)
        df_missing.to_csv('non_trovati.csv', index=False, encoding='utf-8')
        print("📄 Brani non trovati salvati in 'non_trovati.csv'.")

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
