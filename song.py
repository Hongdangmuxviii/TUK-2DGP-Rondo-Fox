"""채보 읽기와 음악 시계."""
import json

from pico2d import get_time, load_music

import config


STAGES = {
    1: dict(
        chart=('music', 'charts', 'stage1_intro_chart.json'),
        audio=('music', 'stage1_intro.mp3'),
        background=('background', 'bg_stage1.png'), bg_tile=966,
        numeral='Ⅰ', name='객석', subtitle='Introduction · Andante malinconico',
        speed=520,             # 노트 속도 (px/초). 느린 서주라 천천히
        bpm=54,
        intro_lines=[('여우', '그분이 연주하던 곡이야. 나도 그분처럼…!'),
                     ('지휘자', '또 그자의 흉내인가. 지겨운 소리다.')],
        fail_line='흉내는 거기까지다.',
    ),
}


def load_chart(stage):
    with open(config.asset(*STAGES[stage]['chart']), encoding='utf-8') as f:
        data = json.load(f)
    notes = sorted(data['notes'], key=lambda n: n['t'])
    return notes, data.get('offset', 0.0)


def _music_call(music, method, sdl_name):
    """pico2d 버전에 따라 Music.pause/resume이 없을 수 있어 SDL_mixer를 직접 부름."""
    if hasattr(music, method):
        getattr(music, method)()
    else:
        import sdl2.sdlmixer as mix
        getattr(mix, sdl_name)()


class SongClock:
    """음악 재생 위치(초). 시작 전에는 음수(LEAD_IN)부터 흐르다가 0이 되는 순간 음악을 튼다."""

    def __init__(self, stage):
        self.music = load_music(config.asset(*STAGES[stage]['audio']))
        self.music.set_volume(100)
        self.started = False       # 시계가 흐르기 시작했는지
        self.playing = False       # 음악이 실제로 나오는 중인지
        self.base = 0.0            # time = get_time() - base
        self.paused_at = None
        self.offset = config.AUDIO_OFFSET

    def start(self, lead_in=config.LEAD_IN):
        self.started = True
        self.base = get_time() + lead_in

    @property
    def time(self):
        if not self.started:
            return -config.LEAD_IN
        now = self.paused_at if self.paused_at is not None else get_time()
        return now - self.base - self.offset

    def update(self):
        if self.started and not self.playing and self.paused_at is None and get_time() >= self.base:
            self.music.play(1)
            self.base = get_time()     # 실제로 튼 순간을 0초로 다시 맞춤
            self.playing = True

    def pause(self):
        if self.paused_at is None:
            self.paused_at = get_time()
            if self.playing:
                _music_call(self.music, 'pause', 'Mix_PauseMusic')

    def resume(self):
        if self.paused_at is not None:
            self.base += get_time() - self.paused_at
            self.paused_at = None
            if self.playing:
                _music_call(self.music, 'resume', 'Mix_ResumeMusic')

    def stop(self):
        self.music.stop()
        self.playing = False
