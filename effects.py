"""한 번 재생하고 사라지는 이펙트들."""
import random

import assets
import config
import game_framework
import game_world


class Effect:
    """pixelfx 시트 한 번 재생. (x, y)는 기준점(대상 발밑)."""

    def __init__(self, name, x, y, delay=0.0, alpha=1.0):
        self.fx = assets.fx(name)
        self.x, self.y = x, y
        self.t = -delay
        self.alpha = alpha
        self.dead = False

    def update(self):
        self.t += game_framework.frame_time
        if self.t > self.fx.total:
            self.dead = True

    def draw(self):
        if self.t >= 0:
            self.fx.draw(self.t, self.x, self.y, alpha=self.alpha)


def spawn(name, x, y, delay=0.0, alpha=1.0):
    game_world.add_object(Effect(name, x, y, delay, alpha), game_world.FX)


class JudgeText:
    """PERFECT / GOOD / MISS 글자. 맞은 줄 판정선 오른쪽 위에서 떠오르며 사라짐."""
    LIFE = 0.45
    FILES = {'PERFECT': 'judge_perfect.png', 'GOOD': 'judge_good.png', 'MISS': 'judge_miss.png'}

    def __init__(self, judge, lane):
        self.img = assets.image('ui', self.FILES[judge])
        # 위 줄은 콤보 숫자와 겹치지 않게 오른쪽으로 비켜 둠
        self.x = config.JUDGE_X + (230 if lane == 'up' else 60) + self.img.w / 2
        self.y = config.LANE_Y[lane] + 150
        self.age = 0.0
        self.dead = False

    def update(self):
        self.age += game_framework.frame_time
        if self.age > self.LIFE:
            self.dead = True

    def draw(self):
        u = self.age / self.LIFE
        pop = 1.0 + 0.25 * max(0.0, 1 - u * 6)          # 처음에 살짝 크게
        a = 1.0 if u < 0.6 else 1 - (u - 0.6) / 0.4
        self.img.opacify(max(0.0, a))
        self.img.draw(self.x, self.y + 60 * u, self.img.w * pop, self.img.h * pop)
        self.img.opacify(1.0)


def judge_text(judge, lane):
    # 같은 줄에 남은 이전 글자는 바로 지움
    for o in game_world.world[game_world.HUD][:]:
        if isinstance(o, JudgeText) and o.y == config.LANE_Y[lane] + 150:
            game_world.remove_object(o)
    game_world.add_object(JudgeText(judge, lane), game_world.HUD)


class Spark:
    """롱노트를 베며 나갈 때 튀는 금빛·진홍 조각 (잉크 방울 그림을 색 없이 작게 사용)."""
    LIFE = 0.35

    def __init__(self, x, y):
        self.img = assets.image('ui', 'progress_fill.png')     # 금색 조각
        self.x, self.y = x + random.uniform(-6, 6), y + random.uniform(-6, 6)
        self.vx, self.vy = random.uniform(-260, -80), random.uniform(-60, 300)
        self.age = 0.0
        self.dead = False

    def update(self):
        dt = game_framework.frame_time
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy -= 1000 * dt
        if self.age > self.LIFE:
            self.dead = True

    def draw(self):
        self.img.opacify(max(0.0, 1 - self.age / self.LIFE))
        self.img.draw(self.x, self.y, 6, 4)
        self.img.opacify(1.0)
