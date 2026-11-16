"""화면 배치와 게임 수치. 좌표는 pico2d 기준(아래가 y=0)."""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.join(ROOT, 'rondo_fox_assets')


def asset(*parts):
    return os.path.join(ASSET, *parts)


W, H = 1280, 720

# 줄 배치
FOX_X = 330            # 여우 발 x
JUDGE_X = 430          # 판정 겹세로줄 x
LOW_Y = 147            # 아래 줄 발 높이 (화면 위에서 573)
UP_Y = LOW_Y + 190     # 위 줄 발 높이
STAFF_DY = 64          # 발 높이 -> 오선 세로 중심
LANE_Y = {'down': LOW_Y, 'up': UP_Y}
LANE_KEY_NAME = {'up': 'F', 'down': 'J'}

# 배율
FOX_SCALE = 0.46
ENEMY_SCALE = 0.40
TAIL_SCALE = 0.32
RIBBON_SCALE = 0.42
FX_SCALE = 2           # pixelfx는 정수 배율
HAND_SCALE = 0.5
BG_SCALE = 0.74
BG_BOTTOM = 3          # 배경 아래 끝 (위로 41 px 올려 그린 결과)
PIT_SCALE = W / 1536
PIT_BOTTOM = -114      # 난간 윗선이 화면 위에서 y=600에 오도록

# 판정 (초)
PERFECT_WINDOW = 0.06
GOOD_WINDOW = 0.13
SCORE_PERFECT = 1000
SCORE_GOOD = 500
COMBO_BONUS = 10       # 콤보 1당 추가 점수 (최대 50콤보까지)

# HP
HP_MAX = 100
HP_MISS = 12
HP_PERFECT_HEAL = 1

# 음원 지연 보정 (초). 노트가 소리보다 늦게 오면 +, 빨리 오면 -.
# 플레이 중 [ ] 키로 0.01초씩 조절 가능.
AUDIO_OFFSET = 0.0
LEAD_IN = 2.0          # 음악 시작 전 노트가 다가오는 여유 시간

FONT = asset('fonts', 'NotoSerifKR-Bold-subset.otf')

GOLD = (240, 198, 110)
CREAM = (250, 238, 210)
INK = (30, 16, 24)
SKY = (190, 225, 255)
