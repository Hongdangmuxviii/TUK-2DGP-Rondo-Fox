"""플레이 화면 HUD. ASSETS.md 좌표(위가 0)를 pico2d 좌표로 바꿔 그림."""
import assets
import config
from config import CREAM, GOLD, H, JUDGE_X, LANE_Y, STAFF_DY


def top(y, h):
    """위 기준 y와 높이 -> pico2d 중심 y"""
    return H - y - h / 2


class Score:
    def __init__(self, total_judges):
        self.total = total_judges
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.counts = {'PERFECT': 0, 'GOOD': 0, 'MISS': 0}
        self.hp = config.HP_MAX

    def add(self, judge):
        self.counts[judge] += 1
        if judge == 'MISS':
            self.combo = 0
            return
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        base = config.SCORE_PERFECT if judge == 'PERFECT' else config.SCORE_GOOD
        self.score += base + min(self.combo, 50) * config.COMBO_BONUS
        if judge == 'PERFECT':
            self.hp = min(config.HP_MAX, self.hp + config.HP_PERFECT_HEAL)

    def damage(self):
        self.hp = max(0, self.hp - config.HP_MISS)

    @property
    def judged(self):
        return sum(self.counts.values())

    @property
    def accuracy(self):
        if not self.judged:
            return 100.0
        return (self.counts['PERFECT'] * 100 + self.counts['GOOD'] * 60) / self.judged

    def rank(self):
        a = self.accuracy
        if self.counts['MISS'] == 0 and self.counts['GOOD'] == 0:
            return 'S+'
        return 'S' if a >= 95 else 'A' if a >= 88 else 'B' if a >= 75 else 'C' if a >= 60 else 'D'


class HUD:
    def __init__(self, score, clock, stage_info, duration):
        self.score, self.clock, self.info, self.duration = score, clock, stage_info, duration
        im = lambda n: assets.image('ui', n)
        self.shade, self.hp_frame, self.hp_fill, self.hp_frets = \
            im('top_shade.png'), im('hp_frame.png'), im('hp_fill.png'), im('hp_frets.png')
        self.p_staff, self.p_fill, self.p_marker = im('progress_staff.png'), im('progress_fill.png'), im('progress_marker.png')
        self.pause_img, self.pause_hover = im('pause_button.png'), im('pause_button_hover.png')
        self.combo_label = im('combo_label.png')
        self.hover = False
        self.shown_hp = float(score.hp)
        self.offset_msg_t = 0.0

    def pause_button_hit(self, x, y):
        """pico2d 좌표 (x, y)가 일시정지 버튼 위인지"""
        return 1207 <= x <= 1259 and H - 73 <= y <= H - 21

    def update(self):
        import game_framework
        dt = game_framework.frame_time
        self.shown_hp += (self.score.hp - self.shown_hp) * min(1.0, dt * 10)
        self.offset_msg_t = max(0.0, self.offset_msg_t - dt)

    def draw(self):
        self.shade.draw(640, top(0, 90))
        self.draw_hp()
        self.draw_progress()
        b = self.pause_hover if self.hover else self.pause_img
        b.draw(1207 + 26, top(21, 52))
        # 스테이지 이름 (왼쪽 위)
        assets.text(28, self.info['numeral'], 24, H - 52, GOLD)
        assets.text(20, self.info['name'], 58, H - 50, CREAM)
        assets.text(13, self.info['subtitle'], 58, H - 72, (240, 215, 170))
        # 점수 / 정확도 (오른쪽 끝 x 1188)
        assets.text(30, f'{self.score.score:,}', 1188, H - 58, CREAM, outline_px=3, align='right')
        assets.text(17, f'정확도 {self.score.accuracy:.1f}%', 1188, H - 90, GOLD, align='right')
        # 콤보: 왼쪽 끝 = 판정선 x 426, 아랫선 = 위 줄 오선 맨 윗선 + 22
        if self.score.combo >= 2:
            base = LANE_Y['up'] + STAFF_DY + 24 + 22
            w = assets.text(46, str(self.score.combo), JUDGE_X - 4, base, CREAM, outline_px=3)
            self.combo_label.draw(JUDGE_X - 4 + w + 10 + self.combo_label.w / 2, base + 9)
        if self.offset_msg_t > 0:
            assets.text(15, f'싱크 보정 {self.clock.offset * 1000:+.0f} ms', 1188, H - 110, CREAM, align='right')

    def draw_hp(self):
        self.hp_frame.draw(22 + 26, top(100, 440))
        r = max(0.0, min(1.0, self.shown_hp / config.HP_MAX))
        if r > 0:
            h = int(360 * r)
            bottom = H - 158 - 360
            self.hp_fill.clip_draw(0, 0, 32, h, 32 + 16, bottom + h / 2)
        self.hp_frets.draw(30 + 18, top(156, 364))

    def draw_progress(self):
        x0, w = 416, 448
        self.p_staff.draw(x0 + w / 2, top(24, 40))
        p = max(0.0, min(1.0, self.clock.time / self.duration))
        if p > 0:
            self.p_fill.draw(x0 + w * p / 2, top(42, 4), w * p, 4)
        self.p_marker.draw(x0 + w * p, H - 44)
