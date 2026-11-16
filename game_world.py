"""그리는 순서별 레이어."""

BG, STAFF, NOTE, FOX, FX, PIT, CONDUCTOR, HUD = range(8)
world = [[] for _ in range(8)]


def add_object(o, depth):
    world[depth].append(o)


def remove_object(o):
    for layer in world:
        for i, item in enumerate(layer):
            if item is o:
                del layer[i]
                return


def update():
    for layer in world:
        for o in layer[:]:
            o.update()
            if getattr(o, 'dead', False):
                remove_object(o)


def render():
    for layer in world:
        for o in layer:
            o.draw()


def clear():
    for layer in world:
        layer.clear()
