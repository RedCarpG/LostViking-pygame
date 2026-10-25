from pygame.locals import K_w, K_s, K_a, K_d, K_UP, K_DOWN, K_LEFT, K_RIGHT, K_SPACE, K_q, K_e, \
    K_KP8, K_KP5, K_KP4, K_KP6, K_KP0, K_RCTRL, K_RSHIFT


class PLAYER1_CONTROL:
    """ Keys of each action: any key of the tuple works """
    MOVE_UP = (K_w, K_UP)
    MOVE_DOWN = (K_s, K_DOWN)
    MOVE_LEFT = (K_a, K_LEFT)
    MOVE_RIGHT = (K_d, K_RIGHT)
    SHOOT = (K_SPACE,)
    BOMB = (K_q,)
    # Switch weapons (the Viking transforms)
    SWITCH = (K_e,)


class PLAYER2_CONTROL:
    """ Not used yet (one player game) """
    MOVE_UP = (K_KP8,)
    MOVE_DOWN = (K_KP5,)
    MOVE_LEFT = (K_KP4,)
    MOVE_RIGHT = (K_KP6,)
    SHOOT = (K_RCTRL,)
    BOMB = (K_RSHIFT,)
    SWITCH = (K_KP0,)
