"""무대: 배경, 오선과 판정선, 피트 전경, 지휘자 손, 잉크 방울."""
import math
import random

import assets
import config
import game_framework
from config import JUDGE_X, LANE_Y, STAFF_DY, W


class Background:
    def __init__(self, path, tile_w, speed):
        self.img = assets.image(*path)
        self.tile_w = tile_w * config.BG_SCALE
        self.h = self.img.h * config.BG_SCALE
        self.speed = speed * 0.4
        self.scroll = 0.0
        self.moving = False

    def update(self):
        if self.moving:
            self.scroll += self.speed * game_framework.frame_time

    def draw(self):
        x = -(self.scroll % self.tile_w)
        while x < W:
            self.img.draw_to_origin(x, config.BG_BOTTOM, self.tile_w + 1, self.h)
            x += self.tile_w


class PitForeground:
    def __init__(self):
        self.img = assets.image('conductor', 'pit_foreground.png')

    def update(self):
        pass

    def draw(self):
        self.img.draw_to_origin(0, config.PIT_BOTTOM, W, self.img.h * config.PIT_SCALE)


class JudgeLine:
    """두 줄의 오선 + 판정 겹세로줄. 박자마다 뒤쪽 빛이 깜빡임."""

    def __init__(self, clock, bpm):
        self.clock = clock
        self.beat = 60 / bpm
        self.staff = assets.image('ui', 'staff_lines.png')
        self.bar = assets.image('ui', 'judge_barline.png')
        self.glow = assets.image('ui', 'judge_glow.png')
        self.link = assets.image('ui', 'progress_fill.png')
        self.flash = {'up': 0.0, 'down': 0.0}     # 맞았을 때 잠깐 밝게

    def hit(self, lane):
        self.flash[lane] = 0.18

    def update(self):
        for k in self.flash:
            self.flash[k] = max(0.0, self.flash[k] - game_framework.frame_time)

    def draw(self):
        t = self.clock.time
        pulse = max(0.0, 1 - ((t % self.beat) / self.beat) * 3) if t >= 0 else 0.0
        for lane, y in LANE_Y.items():
            cy = y + STAFF_DY
            self.staff.draw(JUDGE_X - 4 + self.staff.w / 2, cy)
            a = min(1.0, 0.35 + 0.5 * pulse + self.flash[lane] * 4)
            self.glow.opacify(a)
            self.glow.draw(JUDGE_X + 4, cy)
            self.glow.opacify(1.0)
            self.bar.draw(JUDGE_X - 14.5, cy)      # 굵은 줄 중심(칸 안 x 34.5)이 판정 x
        # 두 오선을 잇는 가는 금색 선
        y0, y1 = LANE_Y['down'] + STAFF_DY + 26, LANE_Y['up'] + STAFF_DY - 26
        self.link.opacify(0.45)
        self.link.draw(JUDGE_X, (y0 + y1) / 2, 2, y1 - y0)
        self.link.opacify(1.0)


class Conductor:
    """해골 지휘자 오른손. 평소엔 숨쉬기, 특수 몹·롱노트 전에만 손목 스냅으로 휘저음."""
    SWEEP = [(1, 0.12), (2, 0.08), (3, 0.15)]       # (프레임, 시간) 이후 0번으로
    ANCHOR = (610, 511)
    POS = (900, -40)

    def __init__(self, clock):
        self.clock = clock
        self.sheet = assets.Sheet(('conductor', 'conductor_sweep.png'), 2, 2, 768, 512)
        self.queue = []          # (휘젓기 시작 음악 시간, 잉크가 날아갈 줄)
        self.active = None       # (시작 시간, 줄, 잉크 뿌렸는지)
        self.real_t = 0.0

    def schedule(self, start_time, lane):
        self.queue.append((start_time, lane))
        self.queue.sort()

    def frame(self):
        if not self.active:
            return 0
        a = self.clock.time - self.active[0]
        acc = 0.0
        for i, d in self.SWEEP:
            acc += d
            if a < acc:
                return i
        return 0

    def update(self):
        self.real_t += game_framework.frame_time
        t = self.clock.time
        if self.queue and t >= self.queue[0][0]:
            start, lane = self.queue.pop(0)
            self.active = [start, lane, False]
        if self.active:
            f = self.frame()
            if f == 2 and not self.active[2]:
                self.active[2] = True
                self.throw_ink(self.active[1])
            if t - self.active[0] > sum(d for _, d in self.SWEEP):
                self.active = None

    def throw_ink(self, lane):
        import game_world
        s = config.HAND_SCALE
        tip = (self.POS[0] - self.ANCHOR[0] * s + 40 * s, self.POS[1] + (self.ANCHOR[1] - 300) * s)
        for k in range(10):
            target = (1180 + random.uniform(-40, 60), LANE_Y[lane] + 60 + random.uniform(-100, 30))
            game_world.add_object(InkDrop(tip, target, k * 0.02), game_world.CONDUCTOR)

    def draw(self):
        f = self.frame()
        breathe = 0 if f else 1.5 * math.sin(2 * math.pi * self.real_t / 2.0)
        self.sheet.draw(f, self.POS[0], self.POS[1] + breathe, self.ANCHOR[0], self.ANCHOR[1], config.HAND_SCALE)


class InkDrop:
    LIFE = 0.5

    def __init__(self, start, target, delay):
        self.img = assets.image('objects', 'ink_drop.png')
        self.start, self.target = start, target
        self.age = -delay
        self.size = random.uniform(0.55, 0.9)
        self.dead = False

    def update(self):
        self.age += game_framework.frame_time
        if self.age > self.LIFE:
            self.dead = True

    def draw(self):
        if self.age < 0:
            return
        u = self.age / self.LIFE
        x = self.start[0] + (self.target[0] - self.start[0]) * u
        y = self.start[1] + (self.target[1] - self.start[1]) * u + 170 * math.sin(math.pi * u)
        k = self.size * (1 - 0.5 * u)
        self.img.opacify(1 - 0.4 * u)
        self.img.draw(x, y, 24 * k, 24 * k)
        self.img.opacify(1.0)
