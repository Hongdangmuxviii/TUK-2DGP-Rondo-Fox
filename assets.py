"""이미지·시트·이펙트·글자 로딩 (한 번만 읽고 재사용)."""
import json

import pico2d
from pico2d import load_image, load_font

import config

try:   # 축소해서 그리는 그림은 부드럽게, 픽셀 이펙트는 각지게
    from sdl2 import SDL_SetHint, SDL_HINT_RENDER_SCALE_QUALITY
except ImportError:
    SDL_SetHint = None

_images = {}


def image(*path, smooth=True):
    key = (path, smooth)
    if key not in _images:
        if SDL_SetHint:
            SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, b'1' if smooth else b'0')
        _images[key] = load_image(config.asset(*path))
    return _images[key]


def draw_at(img, sx, sy, sw, sh, x, y, ax, ay, scale, alpha=1.0):
    """시트의 한 칸(sx, sy는 왼쪽 위 기준)을 그 칸 안의 점 (ax, ay)가 화면 (x, y)에 오도록 그림."""
    cx = x + (sw / 2 - ax) * scale
    cy = y + (ay - sh / 2) * scale
    if alpha < 1.0:
        img.opacify(max(0.0, alpha))
    img.clip_draw(int(sx), int(img.h - sy - sh), int(sw), int(sh), cx, cy, sw * scale, sh * scale)
    if alpha < 1.0:
        img.opacify(1.0)


class Sheet:
    """같은 크기 칸이 격자로 놓인 스프라이트 시트."""

    def __init__(self, path, cols, rows, fw, fh, smooth=True):
        self.img = image(*path, smooth=smooth)
        self.cols, self.rows, self.fw, self.fh = cols, rows, fw, fh

    def draw(self, i, x, y, ax, ay, scale, alpha=1.0):
        col, row = i % self.cols, i // self.cols
        draw_at(self.img, col * self.fw, row * self.fh, self.fw, self.fh, x, y, ax, ay, scale, alpha)


class PixelFX:
    """patch-gg/pixelfx 시트 (JSON에 프레임 사각형, 시간, 기준점)."""

    def __init__(self, name):
        with open(config.asset('effects', 'pixelfx', name + '.json'), encoding='utf-8') as f:
            data = json.load(f)
        self.img = image('effects', 'pixelfx', name + '.png', smooth=False)
        self.frames = [fr['frame'] for fr in data['frames']]
        self.durations = [fr['duration'] / 1000 for fr in data['frames']]
        self.pivot = data['meta']['pixelfx']['pivot']
        self.total = sum(self.durations)

    def frame_at(self, t):
        acc = 0.0
        for i, d in enumerate(self.durations):
            acc += d
            if t < acc:
                return i
        return None

    def draw(self, t, x, y, scale=config.FX_SCALE, alpha=1.0):
        i = self.frame_at(t)
        if i is None:
            return False
        f = self.frames[i]
        draw_at(self.img, f['x'], f['y'], f['w'], f['h'], x, y, self.pivot[0], self.pivot[1], scale, alpha)
        return True


_fx = {}


def fx(name):
    if name not in _fx:
        _fx[name] = PixelFX(name)
    return _fx[name]


# ---------- 글자 ----------
_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = load_font(config.FONT, size)
    return _fonts[size]


_text_cache = {}


def _render(size, s, color):
    """글자를 한 번 그림으로 만들어 캐시. pico2d Font.draw는 매번 텍스처를 새로 만들어서 느림."""
    key = (size, s, color)
    if key in _text_cache:
        return _text_cache[key]
    f = font(size)
    if hasattr(pico2d, 'render_text_image'):           # 테스트용 가짜 pico2d
        img = pico2d.render_text_image(f, s, color)
    else:
        from sdl2 import SDL_Color, SDL_CreateTextureFromSurface, SDL_FreeSurface
        from sdl2.sdlttf import TTF_RenderUTF8_Blended
        if SDL_SetHint:
            SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, b'1')
        surface = TTF_RenderUTF8_Blended(f.font, s.encode('utf-8'), SDL_Color(*color))
        texture = SDL_CreateTextureFromSurface(pico2d.renderer, surface)
        SDL_FreeSurface(surface)
        img = pico2d.Image(texture)
    if len(_text_cache) > 600:
        _text_cache.clear()
    _text_cache[key] = img
    return img


def font_metrics(size):
    f = font(size)
    if hasattr(pico2d, 'font_metrics'):
        return pico2d.font_metrics(f)
    from sdl2.sdlttf import TTF_FontAscent, TTF_FontDescent
    return TTF_FontAscent(f.font), -TTF_FontDescent(f.font)


def text_width(size, s):
    return _render(size, s, (255, 255, 255)).w if s else 0


def text(size, s, x, baseline, color, outline=config.INK, outline_px=2, align='left', alpha=1.0):
    """x와 글자 아랫선(baseline) 기준으로 그림. align: left / right / center."""
    if not s:
        return
    img = _render(size, s, color)
    ascent, descent = font_metrics(size)
    w = img.w
    left = x if align == 'left' else (x - w if align == 'right' else x - w / 2)
    cx = left + w / 2
    cy = baseline + (ascent - descent) / 2 - (ascent + descent - img.h) / 2
    if outline:
        o = _render(size, s, outline)
        if alpha < 1.0:
            o.opacify(alpha)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            o.draw(cx + dx * outline_px, cy + dy * outline_px)
        if alpha < 1.0:
            o.opacify(1.0)
    if alpha < 1.0:
        img.opacify(alpha)
    img.draw(cx, cy)
    if alpha < 1.0:
        img.opacify(1.0)
    return w
