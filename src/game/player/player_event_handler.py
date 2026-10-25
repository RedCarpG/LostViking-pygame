import pygame.event

from src.helper.sound import play_sound
from src.game.animation import FloatingText
from src.game.animation.FloatingText import WARNING_COLOR
from src.game.custom_events import EVENT_PLAYER_SHOOT, EVENT_PLAYER_BOMB, EVENT_BOMB_EXPLODE
from .PlayerPlane import PlayerPlane
from .PlayerBomb import PlayerNucBomb


def _handle_player_shoot_event(player: PlayerPlane):
    player.attack()


def _handle_player_bomb_launch_event(player: PlayerPlane):
    if player.in_stasis:
        play_sound("BOMB_ERROR")
    elif player.bomb_count > 0:
        player.dec_bomb()
        PlayerNucBomb.launch(player.pos, player)
        pygame.event.set_blocked(EVENT_PLAYER_BOMB)
    else:
        play_sound("BOMB_ERROR")
        if player.is_active:
            FloatingText((player.rect.centerx, player.rect.top - 10), "NO BOMBS", WARNING_COLOR)


def _handle_player_bomb_explode_event(player: PlayerPlane):
    from src.game.groups import G_Enemys, G_Enemy_Bullets
    for each in G_Enemys:
        if each.is_active:
            # The blast goes through shields
            each.hit(1000, ignore_shield=True)
            if not each.is_active:
                player.credit_kill(each)

    for each in G_Enemy_Bullets:
        each.hit()

    pygame.event.set_allowed(EVENT_PLAYER_BOMB)


def reset_player_events():
    """ Reset the player event states, called when a round restarts """
    PlayerNucBomb._IS_LAUNCHED = False
    pygame.event.set_allowed(EVENT_PLAYER_BOMB)


def detect_custom_event(e: pygame.event.Event):
    # --------------- Customized Events ---------------
    if e.type == EVENT_PLAYER_SHOOT:
        if hasattr(e, "player"):
            _handle_player_shoot_event(e.player)

    elif e.type == EVENT_PLAYER_BOMB:
        if hasattr(e, "player"):
            _handle_player_bomb_launch_event(e.player)
    elif e.type == EVENT_BOMB_EXPLODE:
        if hasattr(e, "player"):
            _handle_player_bomb_explode_event(e.player)
    else:
        return False
    return True
