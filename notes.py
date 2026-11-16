"""흘러오는 적(노트). 아래 줄 = 잉크 음표, 위 줄 = 쉼표 유령 / 금빛 장식음, 롱노트 = 붙임줄 리본."""
import assets
import config
import game_framework
from config import JUDGE_X, LANE_Y, W

# 종류별: 파일, 배율, 칸 안 발 높이(ay), 터짐 프레임 시간
KINDS = {
    'ink': dict(file='enemy_ink', scale=config.ENEMY_SCALE, ay=470, burst=(0.07, 0.07, 0.07, 0.07)),
    'ghost': dict(file='rest_ghost', scale=config.ENEMY_SCALE, ay=300, burst=(0.09, 0.07, 0.07, 0.12)),
    'gold': dict(file='gold_grace', scale=0.36, ay=340, burst=(0.06, 0.06, 0.07, 0.12)),
}
X_SHIFT = 30          # 몸통이 판정점보다 살짝 오른쪽에 오도록


class Enemy:
    """적 한 마리 그리기 (대기 반복 / 맞고 터짐 / 하얀 번쩍임)."""

    def __init__(self, kind, scale=None):
        k = KINDS[kind]
        self.sheet = assets.Sheet(('objects', k['file'] + '.png'), 4, 2, 384, 512)
        self.flash = assets.Sheet(('objects', k['file'] + '_flash.png'), 4, 2, 384, 512)
        self.scale = scale or k['scale']
        self.ay = k['ay']
        self.burst = k['burst']

    def draw_idle(self, x, y, t, alpha=1.0):
        ax = 192 - X_SHIFT / self.scale
        self.sheet.draw(int(t / 0.125) % 4, x, y, ax, self.ay, self.scale, alpha)

    def burst_length(self):
        return sum(self.burst)

    def draw_burst(self, x, y, age):
        """맞은 뒤 age초. 끝났으면 False."""
        acc = 0.0
        for i, d in enumerate(self.burst):
            acc += d
            if age < acc:
                self.sheet.draw(4 + i, x, y, 192, self.ay, self.scale)
                if age < 0.06:
                    self.flash.draw(4 + i, x, y, 192, self.ay, self.scale, 0.9)
                return True
        return False


class Note:
    def __init__(self, data, speed, clock, kind):
        self.t = data['t']
        self.lane = data['lane']
        self.speed = speed
        self.clock = clock
        self.y = LANE_Y[self.lane]
        self.enemy = Enemy(kind)
        self.state = 'alive'       # alive / hit / missed / done
        self.hit_age = 0.0
        self.anim_t = 0.0
        self.dead = False

    @property
    def is_long(self):
        return False

    def x_at(self, t):
        return JUDGE_X + (t - self.clock.time) * self.speed

    def on_hit(self):
        self.state = 'hit'
        self.hit_age = 0.0

    def on_miss(self):
        self.state = 'missed'

    def update(self):
        dt = game_framework.frame_time
        self.anim_t += dt
        if self.state == 'hit':
            self.hit_age += dt
            if self.hit_age > self.enemy.burst_length():
                self.dead = True
        elif self.state == 'missed' and self.x_at(self.t) < -150:
            self.dead = True

    def draw(self):
        if self.state == 'hit':
            self.enemy.draw_burst(JUDGE_X + 40, self.y, self.hit_age)
            return
        x = self.x_at(self.t)
        if x > W + 200:
            return
        self.enemy.draw_idle(x, self.y, self.anim_t, 0.55 if self.state == 'missed' else 1.0)


class LongNote(Note):
    """붙임줄(타이)로 이어진 두 적. 머리를 베고 꼬리까지 누르고 있으면 성공."""

    def __init__(self, data, speed, clock, kind):
        super().__init__(data, speed, clock, kind)
        self.end = data['end']
        self.tail = Enemy('ink', config.TAIL_SCALE)
        self.ribbon = assets.image('objects', 'tie_ribbon.png')
        self.ribbon_y = self.y + 120 * config.ENEMY_SCALE
        self.holding = False
        self.tail_state = 'alive'    # alive / hit / missed
        self.tail_age = 0.0

    @property
    def is_long(self):
        return True

    def on_hit(self):
        super().on_hit()
        self.holding = True

    def on_tail(self, ok):
        self.holding = False
        self.tail_state = 'hit' if ok else 'missed'
        self.tail_age = 0.0

    def on_miss(self):                # 머리를 놓치면 리본째 흘러감
        self.state = 'missed'
        self.tail_state = 'missed'

    def update(self):
        dt = game_framework.frame_time
        self.anim_t += dt
        if self.state == 'hit':
            self.hit_age += dt
        if self.tail_state == 'hit':
            self.tail_age += dt
        head_done = self.state == 'missed' or self.hit_age > self.enemy.burst_length()
        tail_done = (self.tail_state == 'hit' and self.tail_age > self.tail.burst_length()) or \
                    (self.tail_state == 'missed' and self.x_at(self.end) < -150)
        if head_done and tail_done:
            self.dead = True

    def draw_ribbon(self, x0, x1, alpha):
        if x1 <= x0:
            return
        s = config.RIBBON_SCALE
        tw, th = self.ribbon.w * s, self.ribbon.h * s
        if alpha < 1.0:
            self.ribbon.opacify(alpha)
        x = x0
        while x < min(x1, W + 10):
            seg = min(tw, x1 - x)
            self.ribbon.clip_draw(0, 0, int(seg / s), self.ribbon.h, x + seg / 2, self.ribbon_y, seg, th)
            x += tw
        if alpha < 1.0:
            self.ribbon.opacify(1.0)

    def draw(self):
        hx, tx = self.x_at(self.t), self.x_at(self.end)
        faded = self.tail_state == 'missed'
        if self.tail_state != 'hit':
            x0 = JUDGE_X if self.holding else hx
            self.draw_ribbon(x0, tx, 0.5 if faded else 1.0)
        # 머리
        if self.state == 'hit':
            self.enemy.draw_burst(JUDGE_X + 40, self.y, self.hit_age)
        elif hx < W + 200:
            self.enemy.draw_idle(hx, self.y, self.anim_t, 0.55 if faded else 1.0)
        # 꼬리
        if self.tail_state == 'hit':
            self.tail.draw_burst(JUDGE_X + 40, self.y, self.tail_age)
        elif tx < W + 200:
            self.tail.draw_idle(tx - 10, self.y, self.anim_t + 0.3, 0.55 if faded else 1.0)
