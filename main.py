import pico2d
from pico2d import close_canvas, open_canvas

import config
import game_framework
import play_mode

open_canvas(config.W, config.H)
if hasattr(pico2d, 'hide_lattice'):
    pico2d.hide_lattice()
game_framework.run(play_mode)
close_canvas()
