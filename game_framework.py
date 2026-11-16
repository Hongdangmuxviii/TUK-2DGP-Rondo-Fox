"""수업 game_framework 구조: 모드 스택 + 메인 루프."""
import time

running = None
stack = None
frame_time = 0.0


def change_mode(mode):
    global stack
    if stack:
        stack[-1].finish()
        stack.pop()
    stack.append(mode)
    mode.init()


def push_mode(mode):
    global stack
    if stack:
        stack[-1].pause()
    stack.append(mode)
    mode.init()


def pop_mode():
    global stack
    if stack:
        stack[-1].finish()
        stack.pop()
    if stack:
        stack[-1].resume()


def quit():
    global running
    running = False


def run(start_mode):
    global running, stack, frame_time
    running = True
    stack = [start_mode]
    start_mode.init()

    current_time = time.time()
    while running:
        stack[-1].handle_events()
        stack[-1].update()
        stack[-1].draw()
        now = time.time()
        frame_time = min(now - current_time, 0.1)   # 창을 끄는 등 멈췄을 때 튀지 않게
        current_time = now

    while stack:
        stack[-1].finish()
        stack.pop()
