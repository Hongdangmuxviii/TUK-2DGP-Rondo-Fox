"""결과 화면 (클리어: 승리 포즈 / 실패: 쓰러진 모습)."""
from pico2d import (SDL_KEYDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_RETURN, SDLK_SPACE, SDLK_r,
                    clear_canvas, get_events, update_canvas)

import assets
import config
import game_framework
import song
from config import CREAM, GOLD, H, LOW_Y, W
from fox import victory_frame

stage = 1
cleared = True
score = None
t = 0.0
bg = dim = fox_sheet = None


def setup(stage_no, ok, sc):
    global stage, cleared, score
    stage, cleared, score = stage_no, ok, sc


def init():
    global t, bg, dim, fox_sheet
    t = 0.0
    bg = assets.image(*song.STAGES[stage]['background'])
    dim = assets.image('ui', 'dim.png')
    name = 'victory' if cleared else 'fall'
    fox_sheet = assets.Sheet(('character', f'fox_{name}.png'), 3, 2, 456, 448)


def finish():
    pass


def pause():
    pass


def resume():
    pass


def handle_events():
    import play_mode
    for e in get_events():
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type == SDL_KEYDOWN and t > 0.6:
            if e.key in (SDLK_r, SDLK_RETURN, SDLK_SPACE):
                game_framework.change_mode(play_mode)
            elif e.key == SDLK_ESCAPE:
                game_framework.quit()


def update():
    global t
    t += game_framework.frame_time


def draw():
    clear_canvas()
    tile = song.STAGES[stage]['bg_tile'] * config.BG_SCALE
    x = 0
    while x < W:
        bg.draw_to_origin(x, config.BG_BOTTOM, tile + 1, bg.h * config.BG_SCALE)
        x += tile
    dim.opacify(0.55)
    dim.draw(W / 2, H / 2, W, H)
    dim.opacify(1.0)

    s = 0.62
    if cleared:
        fox_sheet.draw(victory_frame(t), 330 + 35 * s, LOW_Y - 20, 228, 423, s)
    else:
        fox_sheet.draw(5, 330 + 22 * s, LOW_Y - 20, 228, 423, s)

    info = song.STAGES[stage]
    title = 'STAGE CLEAR' if cleared else 'STAGE FAILED'
    assets.text(22, f'{info["numeral"]}  {info["name"]}', 640, 600, CREAM)
    assets.text(52, title, 640, 530, GOLD if cleared else (220, 120, 120), outline_px=3)

    rows = [('점수', f'{score.score:,}'), ('정확도', f'{score.accuracy:.1f}%'), ('최대 콤보', str(score.max_combo)),
            ('PERFECT', str(score.counts['PERFECT'])), ('GOOD', str(score.counts['GOOD'])),
            ('MISS', str(score.counts['MISS']))]
    for i, (k, v) in enumerate(rows):
        y = 460 - i * 42
        assets.text(20, k, 650, y, (240, 215, 170))
        assets.text(24, v, 1000, y, CREAM, align='right')
    if cleared:
        assets.text(20, '랭크', 1060, 460, (240, 215, 170))
        assets.text(72, score.rank(), 1100, 360, GOLD, outline_px=3, align='center')
    if t > 0.6:
        assets.text(16, 'R / ENTER  다시 하기     ESC  끝내기', 640, 120, CREAM)
    update_canvas()
