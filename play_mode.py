"""플레이 화면. 채보대로 적을 흘려보내고 F(위 줄) / J(아래 줄) 입력을 판정."""
from pico2d import (SDL_KEYDOWN, SDL_KEYUP, SDL_MOUSEBUTTONDOWN, SDL_MOUSEMOTION, SDL_QUIT,
                    SDLK_ESCAPE, SDLK_RETURN, SDLK_SPACE, SDLK_f, SDLK_j,
                    clear_canvas, get_events, update_canvas)

import assets
import config
import effects
import game_framework
import game_world
import song
from config import CREAM, GOLD, H, JUDGE_X, LANE_Y, W
from fox import Fox
from hud import HUD, Score
from notes import LongNote, Note
from stage_scene import Background, Conductor, JudgeLine, PitForeground

try:
    from pico2d import SDLK_LEFTBRACKET, SDLK_RIGHTBRACKET
except ImportError:
    SDLK_LEFTBRACKET, SDLK_RIGHTBRACKET = 91, 93

KEY_LANE = {SDLK_f: 'up', SDLK_j: 'down'}

stage = 1
phase = 'intro'          # intro(대사) -> play -> clear / fail
phase_t = 0.0
intro_index = 0
clock = fox = hud = score = judge_line = conductor = background = None
notes = []
held = set()
last_time = 0.0
dim = None


def init():
    global clock, fox, hud, score, judge_line, conductor, background, notes, phase, phase_t, intro_index
    global held, last_time, dim
    game_world.clear()
    info = song.STAGES[stage]
    chart, _ = song.load_chart(stage)
    clock = song.SongClock(stage)
    speed = info['speed']

    background = Background(info['background'], info['bg_tile'], speed)
    game_world.add_object(background, game_world.BG)
    judge_line = JudgeLine(clock, info['bpm'])
    game_world.add_object(judge_line, game_world.STAFF)

    notes = []
    for i, n in enumerate(chart):
        kind = 'ink'
        if n['lane'] == 'up':
            close = [m for m in chart if m['lane'] == 'up' and m is not n and abs(m['t'] - n['t']) < 0.3]
            kind = 'gold' if close else 'ghost'
        note = (LongNote if n['type'] == 'long' else Note)(n, speed, clock, kind)
        notes.append(note)
        game_world.add_object(note, game_world.NOTE)

    fox = Fox()
    game_world.add_object(fox, game_world.FOX)
    game_world.add_object(PitForeground(), game_world.PIT)
    conductor = Conductor(clock)
    game_world.add_object(conductor, game_world.CONDUCTOR)
    # 특수 몹(위 줄)·롱노트가 화면에 들어오기 직전에만 지휘자가 휘저음
    for n in notes:
        if n.is_long or n.lane == 'up':
            appear = n.t - (W + 120 - JUDGE_X) / speed
            conductor.schedule(appear - 0.35 - 0.12, n.lane)

    last_time = max(getattr(n, 'end', n.t) for n in notes)
    score = Score(sum(2 if n.is_long else 1 for n in notes))
    hud = HUD(score, clock, info, last_time + 1.0)
    game_world.add_object(hud, game_world.HUD)

    dim = assets.image('ui', 'dim.png')
    held = set()
    phase, phase_t, intro_index = 'intro', 0.0, 0


def finish():
    if clock:
        clock.stop()
    game_world.clear()


def pause():
    clock.pause()


def resume():
    clock.resume()


# ---------------- 판정 ----------------
def judge_of(dt):
    dt = abs(dt)
    if dt <= config.PERFECT_WINDOW:
        return 'PERFECT'
    if dt <= config.GOOD_WINDOW:
        return 'GOOD'
    return None


def record(judge, lane, hurt=True):
    score.add(judge)
    effects.judge_text(judge, lane)
    if judge == 'MISS':
        if hurt:
            score.damage()
            fox.hurt()
        return
    judge_line.hit(lane)
    y = LANE_Y[lane]
    effects.spawn('crit-hit' if judge == 'PERFECT' else 'hit-spark', JUDGE_X + 20, y + 40)
    effects.spawn('poof', JUDGE_X + 40, y, delay=0.08, alpha=0.8)


def press(lanes):
    now = clock.time
    fox.run()
    slide_lane = None
    for lane in lanes:
        cands = [n for n in notes if n.lane == lane and n.state == 'alive' and abs(n.t - now) <= config.GOOD_WINDOW]
        if not cands:
            continue
        n = min(cands, key=lambda c: c.t)
        j = judge_of(n.t - now)
        n.on_hit()
        record(j, lane)
        if n.is_long:
            slide_lane = lane
    if slide_lane:
        fox.start_slide(slide_lane)
        for lane in lanes:
            if lane != slide_lane:
                fox.attack([lane])
    else:
        fox.attack(lanes)


def release(lane):
    now = clock.time
    for n in notes:
        if n.is_long and n.holding and n.lane == lane:
            j = judge_of(n.end - now) if now < n.end else 'PERFECT'
            n.on_tail(j is not None)
            if j:
                record(j, lane)
            else:
                record('MISS', lane, hurt=False)
            fox.end_slide()


def check_notes():
    now = clock.time
    for n in notes:
        if n.state == 'alive' and now - n.t > config.GOOD_WINDOW:
            n.on_miss()
            record('MISS', n.lane)
            if n.is_long:
                score.add('MISS')          # 꼬리도 같이 놓침 (HP는 한 번만 깎음)
        if n.is_long and n.holding and now >= n.end:
            n.on_tail(True)                # 끝까지 누르고 있으면 꼬리 자동 성공
            record('PERFECT', n.lane)
            fox.end_slide()


# ---------------- 루프 ----------------
def handle_events():
    for e in get_events():
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type == SDL_MOUSEMOTION:
            hud.hover = hud.pause_button_hit(e.x, H - 1 - e.y)
        elif e.type == SDL_MOUSEBUTTONDOWN and hud.pause_button_hit(e.x, H - 1 - e.y) and phase == 'play':
            open_pause()
        elif e.type == SDL_KEYDOWN:
            if e.key == SDLK_ESCAPE:
                if phase in ('play', 'intro'):
                    open_pause()
            elif phase == 'intro' and e.key in (SDLK_SPACE, SDLK_RETURN):
                next_intro_line()
            elif phase == 'play' and e.key in KEY_LANE and KEY_LANE[e.key] not in held:
                held.add(KEY_LANE[e.key])
                press([KEY_LANE[e.key]])
            elif e.key == SDLK_LEFTBRACKET:
                clock.offset -= 0.01
                hud.offset_msg_t = 1.5
            elif e.key == SDLK_RIGHTBRACKET:
                clock.offset += 0.01
                hud.offset_msg_t = 1.5
        elif e.type == SDL_KEYUP and e.key in KEY_LANE:
            lane = KEY_LANE[e.key]
            held.discard(lane)
            if phase == 'play':
                release(lane)


def open_pause():
    import pause_mode
    game_framework.push_mode(pause_mode)


INTRO_LINE_TIME = 2.2


def next_intro_line():
    global intro_index, phase_t, phase
    intro_index += 1
    phase_t = 0.0
    if intro_index >= len(song.STAGES[stage]['intro_lines']):
        phase = 'play'
        clock.start()
        background.moving = True
        fox.run()


def update():
    global phase, phase_t
    phase_t += game_framework.frame_time
    clock.update()
    if phase == 'intro' and phase_t > INTRO_LINE_TIME:
        next_intro_line()
    if phase == 'play':
        check_notes()
        if score.hp <= 0:
            phase, phase_t = 'fail', 0.0
            clock.stop()
            background.moving = False
            fox.fall()
        elif clock.time > last_time + 0.6 and all(n.state != 'alive' and not getattr(n, 'holding', False) for n in notes):
            phase, phase_t = 'clear', 0.0
            fox.win()
    game_world.update()
    if phase == 'clear':
        background.moving = phase_t < 0.8
        if phase_t > 3.2:
            go_result(True)
    elif phase == 'fail' and phase_t > 2.6:
        go_result(False)


def go_result(cleared):
    import result_mode
    result_mode.setup(stage, cleared, score)
    game_framework.change_mode(result_mode)


def draw_subtitle(speaker, line, alpha=1.0):
    dim.opacify(0.55 * alpha)
    dim.draw(W / 2, 92, 760, 70)
    dim.opacify(1.0)
    assets.text(16, speaker, W / 2, 108, GOLD, align='center', alpha=alpha)
    assets.text(22, line, W / 2, 74, CREAM, align='center', alpha=alpha)


def draw():
    clear_canvas()
    game_world.render()
    if phase == 'intro':
        lines = song.STAGES[stage]['intro_lines']
        speaker, line = lines[min(intro_index, len(lines) - 1)]
        a = min(1.0, phase_t / 0.25)
        draw_subtitle(speaker, f'“{line}”', a)
        assets.text(13, 'SPACE 넘기기', W - 24, 24, (240, 220, 190), align='right')
    elif phase == 'play' and clock.time < 1.2:
        a = 1.0 if clock.time < 0.6 else max(0.0, 1 - (clock.time - 0.6) / 0.6)
        assets.text(20, 'F 위 줄   ·   J 아래 줄', W / 2, 92, CREAM, align='center', alpha=a)
    elif phase == 'clear':
        a = min(1.0, phase_t / 0.4)
        assets.text(54, 'STAGE CLEAR', W / 2, 470, GOLD, outline_px=3, align='center', alpha=a)
    elif phase == 'fail':
        a = min(1.0, phase_t / 0.4)
        draw_subtitle('지휘자', f'“{song.STAGES[stage]["fail_line"]}”', a)
    update_canvas()
