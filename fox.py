"""주인공 여우 (상태 기계: 대기 / 달리기 / 베기 / 롱노트 베어 나가기 / 피격 / 쓰러짐 / 승리)."""
import assets
import config
import effects
import game_framework
import game_world
from config import FOX_X, LANE_Y, LOW_Y, UP_Y

S = config.FOX_SCALE


def play_frames(durations, t):
    """durations 순서대로 재생할 때 t초의 프레임 번호. 끝났으면 None."""
    acc = 0.0
    for i, d in enumerate(durations):
        acc += d
        if t < acc:
            return i
    return None


class Idle:
    @staticmethod
    def enter(fox):
        fox.t = 0.0

    @staticmethod
    def do(fox):
        pass

    @staticmethod
    def draw(fox):
        fox.sheets['idle'].draw(int(fox.t / 0.15) % 6, FOX_X, LOW_Y, 228, 423, S)


class Run:
    @staticmethod
    def enter(fox):
        pass

    @staticmethod
    def do(fox):
        pass

    @staticmethod
    def draw(fox):
        fox.sheets['run'].draw(int(fox.t / 0.083) % 8, FOX_X, LOW_Y, 228, 423, S)
        if fox.return_trail > 0:          # 위 줄에서 내려올 때 잔상
            a = fox.return_trail / 0.06
            for k, dy in enumerate((60, 120)):
                fox.sheets['run'].draw(0, FOX_X, UP_Y - dy, 228, 423, S, (0.15 + 0.15 * k) * a)


class Attack:
    FRAMES = [2, 3, 4, 5]                # 키를 누르면 3번(치켜듦)부터
    DURS = [0.06, 0.05, 0.09, 0.08]      # 4번이 타격

    @staticmethod
    def enter(fox):
        fox.attack_t = 0.0

    @staticmethod
    def do(fox):
        fox.attack_t += game_framework.frame_time
        if play_frames(Attack.DURS, fox.attack_t) is None:
            if 'up' in fox.attack_lanes:
                fox.return_trail = 0.06
            fox.change(Run)

    @staticmethod
    def draw(fox):
        i = play_frames(Attack.DURS, fox.attack_t)
        if i is None:
            i = 3
        frame = Attack.FRAMES[i]
        lanes = fox.attack_lanes
        both = len(lanes) == 2
        if 'up' in lanes and fox.attack_t < 0.08:          # 위 줄로 순간이동하는 잔상
            for k, dy in enumerate((60, 120)):
                fox.sheets['ground'].draw(2, FOX_X, LOW_Y + dy, 328, 423, S, 0.25 + 0.15 * k)
        for lane in lanes:
            alpha = 0.55 if (both and lane == 'up') else 1.0
            fox.sheets['ground'].draw(frame, FOX_X, LANE_Y[lane], 328, 423, S, alpha)


class Slide:
    """롱노트: 진입(1) -> 달리며 활 수평 유지(2~5 반복) -> 올려 베기(6)."""

    @staticmethod
    def enter(fox):
        fox.slide_t = 0.0
        fox.slide_end_t = None

    @staticmethod
    def do(fox):
        dt = game_framework.frame_time
        fox.slide_t += dt
        if fox.slide_end_t is not None:
            fox.slide_end_t += dt
            if fox.slide_end_t > 0.24:
                fox.change(Run)
        elif fox.slide_t > 0.08:
            fox.spark_t += dt
            while fox.spark_t > 0.02:
                fox.spark_t -= 0.02
                game_world.add_object(effects.Spark(config.JUDGE_X, fox.slide_y + 120 * config.ENEMY_SCALE),
                                      game_world.FX)

    @staticmethod
    def draw(fox):
        if fox.slide_end_t is not None:
            i = 5
        elif fox.slide_t < 0.08:
            i = 0
        else:
            i = 1 + int((fox.slide_t - 0.08) / 0.083) % 4
        fox.sheets['slide'].draw(i, FOX_X, fox.slide_y, 228, 483, S)


class Hit:
    DURS = [0.06, 0.10, 0.08, 0.06]

    @staticmethod
    def enter(fox):
        fox.hit_t = 0.0

    @staticmethod
    def do(fox):
        fox.hit_t += game_framework.frame_time
        if fox.hit_t > sum(Hit.DURS) + 0.25:
            fox.change(Run)

    @staticmethod
    def draw(fox):
        i = play_frames(Hit.DURS, fox.hit_t)
        if i is None:                     # 피격 뒤 잠깐 깜빡이며 달리기
            if int(fox.hit_t / 0.05) % 2 == 0:
                fox.sheets['run'].draw(int(fox.t / 0.083) % 8, FOX_X, LOW_Y, 228, 423, S, 0.5)
            else:
                fox.sheets['run'].draw(int(fox.t / 0.083) % 8, FOX_X, LOW_Y, 228, 423, S)
            return
        alpha = 0.6 if int(fox.hit_t / 0.04) % 2 else 1.0
        fox.sheets['hit'].draw(i, FOX_X, LOW_Y, 228, 423, S, alpha)


class Fall:
    DURS = [0.10, 0.10, 0.11, 0.12, 0.15]

    @staticmethod
    def enter(fox):
        fox.fall_t = 0.0

    @staticmethod
    def do(fox):
        fox.fall_t += game_framework.frame_time

    @staticmethod
    def draw(fox):
        i = play_frames(Fall.DURS, fox.fall_t)
        fox.sheets['fall'].draw(5 if i is None else i, FOX_X + 22 * S, LOW_Y, 228, 423, S)


class Victory:
    @staticmethod
    def enter(fox):
        fox.victory_t = 0.0

    @staticmethod
    def do(fox):
        fox.victory_t += game_framework.frame_time

    @staticmethod
    def draw(fox):
        fox.sheets['victory'].draw(victory_frame(fox.victory_t), FOX_X + 35 * S, LOW_Y, 228, 423, S)


def victory_frame(t):
    i = play_frames([0.30, 0.09, 0.16, 0.22], t)
    if i is not None:
        return i
    return [3, 4, 5, 4][int((t - 0.77) / 0.17) % 4]


class Fox:
    def __init__(self):
        sheet = lambda name, c, r, w=456, h=448: assets.Sheet(('character', f'fox_{name}.png'), c, r, w, h)
        self.sheets = {
            'idle': sheet('idle', 3, 2), 'run': sheet('run', 4, 2), 'hit': sheet('hit', 2, 2),
            'fall': sheet('fall', 3, 2), 'victory': sheet('victory', 3, 2),
            'ground': sheet('ground', 6, 1, 556, 448), 'slide': sheet('slide', 6, 1, 556, 508),
        }
        self.t = 0.0
        self.attack_lanes = set()
        self.return_trail = 0.0
        self.slide_y = LOW_Y
        self.spark_t = 0.0
        self.state = Idle
        self.state.enter(self)

    def change(self, state):
        self.state = state
        state.enter(self)

    # ---- 플레이 화면에서 부르는 동작 ----
    def run(self):
        if self.state is Idle:
            self.change(Run)

    def attack(self, lanes):
        if self.state in (Fall, Victory):
            return
        if self.state is Slide and self.slide_end_t is None:
            return                           # 롱노트 누르는 중엔 다른 키로 끊지 않음
        if self.state is Attack and self.attack_t < 0.05:
            self.attack_lanes |= set(lanes)  # 거의 동시에 눌린 두 키는 한 번의 베기로
        else:
            self.attack_lanes = set(lanes)
            self.change(Attack)
        for lane in lanes:
            effects.spawn('sword-slash-rondo', FOX_X + 10, LANE_Y[lane])

    def start_slide(self, lane):
        self.slide_y = LANE_Y[lane]
        self.spark_t = 0.0
        self.change(Slide)

    def end_slide(self):
        if self.state is Slide and self.slide_end_t is None:
            self.slide_end_t = 0.0

    def hurt(self):
        if self.state in (Fall, Victory, Slide):
            return
        self.change(Hit)

    def fall(self):
        self.change(Fall)

    def win(self):
        self.change(Victory)

    def update(self):
        dt = game_framework.frame_time
        self.t += dt
        self.return_trail = max(0.0, self.return_trail - dt)
        self.state.do(self)

    def draw(self):
        self.state.draw(self)
