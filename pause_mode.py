"""일시정지 (플레이 화면 위에 덮어 그림)."""
from pico2d import (SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_q, SDLK_r,
                    SDLK_RETURN, clear_canvas, get_events, update_canvas)

import assets
import game_framework
import game_world
from config import CREAM, GOLD, H, W

dim = None


def init():
    global dim
    dim = assets.image('ui', 'dim.png')


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
        elif e.type == SDL_KEYDOWN:
            if e.key in (SDLK_ESCAPE, SDLK_RETURN):
                game_framework.pop_mode()
            elif e.key == SDLK_r:
                game_framework.pop_mode()
                game_framework.change_mode(play_mode)
            elif e.key == SDLK_q:
                game_framework.quit()
        elif e.type == SDL_MOUSEBUTTONDOWN and play_mode.hud.pause_button_hit(e.x, H - 1 - e.y):
            game_framework.pop_mode()


def update():
    pass


def draw():
    clear_canvas()
    game_world.render()
    dim.opacify(0.6)
    dim.draw(W / 2, H / 2, W, H)
    dim.opacify(1.0)
    assets.text(48, '일시정지', W / 2, H / 2 + 50, GOLD, outline_px=3, align='center')
    assets.text(20, 'ESC  계속하기', W / 2, H / 2 - 10, CREAM, align='center')
    assets.text(20, 'R  처음부터 다시', W / 2, H / 2 - 44, CREAM, align='center')
    assets.text(20, 'Q  게임 끝내기', W / 2, H / 2 - 78, CREAM, align='center')
    update_canvas()
