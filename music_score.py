import argparse
import json
import os
import time
import requests

import cairosvg

import chart

note_sizes = {
    'easy': 2.0,
    'normal': 1.5,
    'hard': 1.25,
    'expert': 1.0,
    'master': 0.875,
}


def get_master_data(key):
    url = '%s/%s.json' % (args.data_host, key)
    print('fetching music data from %s' % url)
    r = requests.get(url)
    if r.status_code != 200:
        print(r.status_code)
        return []
    return r.json()


def parse(music_id, difficulty, theme, savepng=True, title=None, artist=None):
    url = '%s/music/music_score/%04d_01/%s' % (args.asset_host, music_id, difficulty)
    print('fetching score from %s' % url)
    r = requests.get(url)
    if r.status_code != 200:
        print(r.status_code)
        return
    lines = r.text.splitlines()

    data = get_master_data("musics")

    for i in data:
        if i['id'] == music_id:
            music = i
            break
    try:
        if music['composer'] == music['arranger']:
            artist = music['composer']
        elif music['composer'] in music['arranger'] or music['composer'] == '-':
            artist = music['arranger']
        elif music['arranger'] in music['composer'] or music['arranger'] == '-':
            artist = music['composer']
        else:
            artist = '%s / %s' % (music['composer'], music['arranger'])
    except:
        music = {'title': title, 'assetbundleName': 'jacket_s_%03d' % music_id}

    playlevel = '?'
    data = get_master_data("musicDifficulties")
    for i in data:
        if i['musicId'] == music_id and i['musicDifficulty'] == difficulty:
            playlevel = i["playLevel"]

    sus = chart.SUS(
        lines,
        note_size=note_sizes[difficulty],
        note_host='../../notes',
        **({
            'title': music['title'],
            'artist': artist,
            'difficulty': difficulty,
            'playlevel': playlevel,
            'jacket': '%s/music/jacket/%s/%s.webp' % (args.asset_host, music['assetbundleName'], music['assetbundleName'])
        }),
    )

    try:
        with open('rebases/%s.json' % music_id, encoding='utf-8') as f:
            rebase = json.load(f)
    except:
        rebase = None

    try:
        with open('rebases/%s.lyric' % music_id, encoding='utf-8') as f:
            sus.words = chart.load_lyric(f.readlines())
    except:
        pass

    if rebase:
        sus.score = sus.score.rebase([
            chart.Event(
                bar=event.get('bar'),
                bpm=event.get('bpm'),
                bar_length=event.get('barLength'),
                sentence_length=event.get('sentenceLength'),
                section=event.get('section'),
            )
            for event in rebase.get('events', [])
        ], offset=rebase.get('offset', 0))

    file_name = '%s/%s/%d/%s' % (args.out_dir, theme, music_id, difficulty)
    os.makedirs(os.path.dirname(file_name), exist_ok=True)

    # themehint = False
    if theme == 'svg' or theme == 'pjskguess':
        with open(f'chart/white/css/sus.css', encoding='utf-8') as f:
            style_sheet = f.read()
        with open(f'chart/white/css/master.css') as f:
            style_sheet += '\n' + f.read()
        # themehint = False
    elif theme == 'color':
        with open(f'chart/{theme}/css/sus.css', encoding='utf-8') as f:
            style_sheet = f.read()
        with open(f'chart/{theme}/css/{difficulty}.css') as f:
            style_sheet += '\n' + f.read()
    else:
        with open(f'chart/{theme}/css/sus.css', encoding='utf-8') as f:
            style_sheet = f.read()
        with open(f'chart/{theme}/css/master.css') as f:
            style_sheet += '\n' + f.read()

    sus.export(file_name + '.svg', style_sheet=style_sheet, display_skill_extra=True)
    if savepng:
        print(file_name)
        cairosvg.svg2png(url=file_name + '.svg', write_to=file_name + '.png', scale=1.3)


if __name__ == '__main__':
    start = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset_host', default='https://asset3.pjsekai.moe')
    parser.add_argument('--data_host',
                        default='https://raw.githubusercontent.com/Sekai-World/sekai-master-db-diff/main')
    parser.add_argument('--out_dir',
                        default='charts/moe')
    parser.add_argument('--music_id', type=int,
                        default=1)
    parser.add_argument('--music_difficulty',
                        default='master')
    args = parser.parse_args()

    parse(args.music_id, args.music_difficulty, 'white')
    print(time.time() - start)
