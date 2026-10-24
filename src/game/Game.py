import asyncio
from enum import Enum
import pygame
from pygame.locals import QUIT, KEYUP, K_TAB, K_F3, K_ESCAPE, K_p, SRCALPHA, \
    WINDOWFOCUSLOST, WINDOWHIDDEN, WINDOWMINIMIZED, WINDOWFOCUSGAINED, WINDOWSHOWN, WINDOWRESTORED
from .custom_events import EVENT_RESTART, EVENT_RESUME, EVENT_START, EVENT_START_TEST, \
    EVENT_MAIN_MENU, EVENT_OPEN_SETTINGS, EVENT_CLOSE_SETTINGS

from src.helper.image import load_image
from src.helper.sound import load_music, play_music
from src.setting import MAIN_VOLUME, SCREEN_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT

from src.game.groups import G_Player1, G_Players, G_BOSS, G_Bomb, G_Enemys, G_Enemy_Bullets, \
    G_Player_Bullets, G_Supplies, G_Effects, G_Texts
from src.game.player import PlayerViking, load_asset_player, detect_custom_event, reset_player_events
from src.game.ui import UI, load_asset_ui, UIIntro, UIPause, UIResult, UISettings, Scoreboard, \
    FPSCounter, Background, TestPanel
from src.game.supply import load_asset_supply, supply_event_config, update_supply_timer, supply_events_handler
from src.game.level import Level1
from src.game.animation import ScreenShake, warmup
from src.game.animation.Explosion import prepare as prepare_explosions
from src.game.GameSettings import GameSettings
from src.game.TestMode import TestMode
from src.util.collide_detect import hit_rect


class GameState(Enum):
    INTRO = 0
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    VICTORY = 4
    SETTINGS = 5


class Game:
    # Frames to wait after the round ends before showing the result screen
    END_DELAY = 120

    # Window (or browser tab) going to the background and coming back
    FOCUS_LOST_EVENTS = [WINDOWFOCUSLOST, WINDOWHIDDEN, WINDOWMINIMIZED]
    FOCUS_GAINED_EVENTS = [WINDOWFOCUSGAINED, WINDOWSHOWN, WINDOWRESTORED]

    # Game logic update interval, and the most updates run for one drawn frame
    UPDATE_MS = 1000 / 60
    MAX_UPDATES = 4
    # Delay that is caught up over the next frames, a longer freeze is skipped
    MAX_LAG_MS = 250
    # Time per menu frame spent preparing rotations and generated effects (see warmup)
    WARMUP_WORK_MS = 6

    # Test mode hitboxes: (group, color, collision ratio used against player bullets / enemy bullets)
    HITBOXES = [
        (G_Enemys, (255, 80, 80), 0.8),
        (G_Enemy_Bullets, (255, 170, 60), 0.6),
        (G_Players, (80, 230, 120), 0.6),
        (G_Player_Bullets, (90, 200, 255), 0.8),
        (G_Supplies, (240, 220, 80), 1.0),
    ]

    def __init__(self) -> None:
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        self.clock = pygame.time.Clock()

        self.running = True
        pygame.mouse.set_visible(True)
        pygame.display.set_icon(load_image("favicon.ico"))

        # Player settings, applied before any sound is loaded
        GameSettings.load()
        GameSettings.apply()

        # Player
        load_asset_player()
        self.player = None
        self._create_player()

        # Supply
        load_asset_supply()

        # Explosions, drawn while the menu is shown (see warmup)
        prepare_explosions()

        # UI
        load_asset_ui()
        self.ui = UI(self.screen)
        self.ui_intro = UIIntro(self.screen)
        self.ui_pause = UIPause(self.screen)
        self.ui_result = UIResult(self.screen)
        self.ui_settings = UISettings(self.screen)
        self.scoreboard = Scoreboard(self.screen)
        self.fps_counter = FPSCounter(
            self.screen, self.clock, [SCREEN_WIDTH-100, 30])
        self.background = Background()
        # Dark layer drawn over the frozen game behind menus
        self.overlay = pygame.Surface(SCREEN_SIZE, SRCALPHA)
        self.overlay.fill((4, 6, 16, 190))
        # The frozen game with the dark layer, made once when a menu opens over the round
        # (drawing the whole world and blending the layer every frame is slow on the web).
        # One surface, reused: _frozen_valid says if it holds the current frozen game
        self._frozen_frame = pygame.Surface(SCREEN_SIZE).convert()
        self._frozen_valid = False

        # Level
        self.level = Level1()
        self.test_panel = TestPanel(self.screen, self)

        self.state = GameState.INTRO
        # State to go back to when the settings screen is closed
        self._settings_return_state = GameState.INTRO
        # Game frames played in the current round (shown on the result screen)
        self._round_frames = 0
        self._count_end_delay = 0
        self._end_state = None

        self._play_intro_music()

    # ------------------ Main loop ------------------

    async def run(self):
        """ The game logic runs 60 times per second of real time. When a frame was slow
        (e.g. the browser stalled), the missed updates are run without drawing them,
        so the game keeps its speed and the controls stay responsive
        """
        lag = 0.0
        last = pygame.time.get_ticks()
        while self.running:
            now = pygame.time.get_ticks()
            lag += now - last
            last = now
            updates = max(1, min(self.MAX_UPDATES, round(lag / self.UPDATE_MS)))
            lag = max(-self.UPDATE_MS, lag - updates * self.UPDATE_MS)
            if lag > self.MAX_LAG_MS:
                # Too far behind (a long freeze, e.g. the tab was hidden): do not catch up
                lag = 0.0
            for i in range(updates):
                self.step(draw=i == updates - 1)
            self.clock.tick(60)
            # Give control back to the browser each frame (required by pygbag)
            await asyncio.sleep(0)

    def step(self, draw=True):
        """ Run one update of the current state, and draw it unless `draw` is False """
        events = pygame.event.get()
        for event in events:
            if event.type in self.FOCUS_LOST_EVENTS:
                self._on_focus_lost()
            elif event.type in self.FOCUS_GAINED_EVENTS:
                self._on_focus_gained()
        if self.state == GameState.INTRO:
            self._step_intro(events)
        elif self.state == GameState.PLAYING:
            self._step_playing(events)
        elif self.state == GameState.PAUSED:
            self._step_paused(events)
        elif self.state == GameState.SETTINGS:
            self._step_settings(events)
        else:
            self._step_result(events)
        if draw:
            self._draw()
            pygame.display.flip()

    def _draw(self):
        if self.state == GameState.INTRO:
            self._draw_intro()
        elif self.state == GameState.PLAYING:
            self._draw_world()
        elif self.state == GameState.SETTINGS:
            if self._settings_return_state == GameState.INTRO:
                self.background.draw(self.screen)
                self.screen.blit(self.overlay, (0, 0))
            else:
                self._draw_frozen_world()
            self.ui_settings.blit()
        else:
            self._draw_frozen_world()
            if self.state == GameState.PAUSED:
                self.ui_pause.blit()
            else:
                self.ui_result.blit()

    def _draw_frozen_world(self):
        """ The paused round, darkened, behind a menu """
        if not self._frozen_valid:
            self._draw_world()
            self.screen.blit(self.overlay, (0, 0))
            self._frozen_frame.blit(self.screen, (0, 0))
            self._frozen_valid = True
        else:
            self.screen.blit(self._frozen_frame, (0, 0))

    # ------------------ States ------------------

    def _step_intro(self, events):
        for event in events:
            if event.type == QUIT:
                self.running = False
            elif self.ui_intro.handle_event(event):
                pass
            elif event.type == EVENT_START:
                self.start_round(test_mode=False)
            elif event.type == EVENT_START_TEST:
                self.start_round(test_mode=True)
            elif event.type == EVENT_OPEN_SETTINGS:
                self.open_settings()

        G_Players.update()
        self.background.update()
        # Prepare the pixel-art rotations and generated effects while the menu is shown
        warmup.work(self.WARMUP_WORK_MS)

    def _step_playing(self, events):
        self._round_frames += 1
        self.player.detect_key_pressed()
        for event in events:
            if event.type == QUIT:
                self.running = False
            elif self.player.handle_event(event):
                pass
            elif detect_custom_event(event):
                self.ui.handle_event(event)
            elif TestMode.enabled and self.test_panel.handle_event(event):
                pass
            # --------------- Key Up Events ---------------
            elif event.type == KEYUP and event.key == K_TAB:
                self.ui.toggle_hidden()
            elif event.type == KEYUP and event.key == K_F3:
                GameSettings.show_fps = not GameSettings.show_fps
                GameSettings.save()
            elif event.type == KEYUP and event.key in (K_ESCAPE, K_p):
                # P too: in a browser Esc first leaves the full screen
                self.pause()
            # --------------- Window Events ---------------
            # Pause when the window (or the browser tab) goes to the background
            elif event.type in [WINDOWFOCUSLOST, WINDOWHIDDEN, WINDOWMINIMIZED]:
                self.pause()
            else:
                supply_events_handler(event)

        G_Enemy_Bullets.update()
        G_Player_Bullets.update()
        G_Players.update()
        G_Supplies.update()
        G_Enemys.update()
        G_Bomb.update()
        G_Effects.update()
        G_Texts.update()
        self.background.update()
        ScreenShake.update()
        self.scoreboard.update()
        if GameSettings.show_fps:
            self.fps_counter.update()
        self.ui.update()
        self.level.update()
        update_supply_timer()

        self._check_round_end()

    def _step_paused(self, events):
        for event in events:
            if event.type == QUIT:
                self.running = False
            elif self.ui_pause.handle_event(event):
                pass
            elif event.type == EVENT_RESUME:
                self.resume()
            elif event.type == EVENT_RESTART:
                self.restart()
                break
            elif event.type == EVENT_OPEN_SETTINGS:
                self.open_settings()
            elif event.type == EVENT_MAIN_MENU:
                self.to_main_menu()
                break

    def _step_settings(self, events):
        for event in events:
            if event.type == QUIT:
                self.running = False
            elif self.ui_settings.handle_event(event):
                pass
            elif event.type == EVENT_CLOSE_SETTINGS:
                self.state = self._settings_return_state
                # Show the new settings (e.g. the FPS counter) on the frozen game
                self._frozen_valid = False

        if self._settings_return_state == GameState.INTRO:
            self.background.update()
            warmup.work(self.WARMUP_WORK_MS)

    def _step_result(self, events):
        for event in events:
            if event.type == QUIT:
                self.running = False
            elif self.ui_result.handle_event(event):
                pass
            elif event.type == EVENT_RESTART:
                self.restart()
                break
            elif event.type == EVENT_MAIN_MENU:
                self.to_main_menu()
                break

    # ------------------ Helpers ------------------

    def _draw_intro(self):
        self.background.draw(self.screen)
        self.ui_intro.blit()
        G_Players.draw(self.screen)

    def _draw_world(self):
        offset = ScreenShake.offset

        self.background.draw(self.screen)
        # Test panel behind the sprites so it never hides them. It is drawn against the
        # shake offset: the world is scrolled afterwards, so the panel ends up still
        if TestMode.enabled:
            self.test_panel.blit(self.screen, offset)
        G_Bomb.draw(self.screen)
        G_Enemy_Bullets.draw(self.screen)
        G_Player_Bullets.draw(self.screen)
        G_Enemys.draw(self.screen)
        G_Players.draw(self.screen)
        G_Supplies.draw(self.screen)
        G_Effects.draw(self.screen)
        G_Texts.draw(self.screen)
        if TestMode.show_hitboxes:
            for group, color, ratio in self.HITBOXES:
                for sprite in group:
                    pygame.draw.rect(self.screen, color, hit_rect(sprite, ratio), 1)

        if offset != (0, 0):
            # Shake: move the drawn world in place (cheaper than drawing it on another
            # surface and copying it), then fill the strips it uncovered
            dx, dy = offset
            self.screen.scroll(dx, dy)
            if dx > 0:
                self.screen.fill(Background.BASE_COLOR, (0, 0, dx, SCREEN_HEIGHT))
            elif dx < 0:
                self.screen.fill(Background.BASE_COLOR, (SCREEN_WIDTH + dx, 0, -dx, SCREEN_HEIGHT))
            if dy > 0:
                self.screen.fill(Background.BASE_COLOR, (0, 0, SCREEN_WIDTH, dy))
            elif dy < 0:
                self.screen.fill(Background.BASE_COLOR, (0, SCREEN_HEIGHT + dy, SCREEN_WIDTH, -dy))

        # HUD on top of the sprites, it does not shake
        self.ui.blit()
        self.scoreboard.blit()
        if GameSettings.show_fps:
            self.fps_counter.blit()

    def _check_round_end(self):
        if self._count_end_delay > 0:
            self._count_end_delay -= 1
            if self._count_end_delay == 0:
                self._show_result(self._end_state)
        elif self.player.is_dead:
            self._end_state = GameState.GAME_OVER
            self._count_end_delay = self.END_DELAY
        elif self.level.is_completed:
            # Keep the player safe from leftover bullets while the boss explodes
            self.player.invincible(continuous=True)
            self._end_state = GameState.VICTORY
            self._count_end_delay = self.END_DELAY

    def _show_result(self, state: GameState):
        self.state = state
        self._frozen_valid = False
        self._stop_player_input()
        pygame.mixer.music.fadeout(1500)
        score = self.player.score
        # Test mode scores do not count
        new_best = not TestMode.enabled and score > GameSettings.best_score
        if new_best:
            GameSettings.best_score = score
            GameSettings.save()
        self.ui_result.show(
            is_victory=state == GameState.VICTORY,
            score=score,
            best_score=GameSettings.best_score,
            new_best=new_best,
            seconds=self._round_frames // 60,
            kills=self.player.kills)

    def _stop_player_input(self):
        """ Release every held control so the player does not keep moving """
        self.player.trigger_stop_x()
        self.player.trigger_stop_y()

    def _create_player(self):
        self.player = PlayerViking(pos=None)
        G_Player1.add(self.player)
        G_Players.add(self.player)

    def _play_intro_music(self):
        load_music("music/bgm.ogg", MAIN_VOLUME - 0.4)
        play_music()

    def _reset_world(self):
        """ Remove everything from the last round and create a new player """
        self._stop_player_input()
        reset_player_events()
        # May come from the pause menu, where the mixer is paused
        pygame.mixer.unpause()
        pygame.mixer.stop()
        supply_event_config()
        ScreenShake.reset()

        # Kill every sprite so it also leaves the per-class groups (e.g. EnemyScout.GROUP)
        for group in [G_BOSS, G_Enemy_Bullets, G_Bomb, G_Effects, G_Texts, G_Enemys,
                      G_Player_Bullets, G_Supplies, G_Player1, G_Players]:
            for sprite in group.sprites():
                sprite.kill()
        pygame.event.clear()

        self._create_player()
        self.ui = UI(self.screen)
        self.scoreboard = Scoreboard(self.screen)

        self._count_end_delay = 0
        self._end_state = None

    def apply_god_mode(self):
        if TestMode.god_mode:
            self.player.invincible(continuous=True)
        else:
            self.player.remove_invincible()

    # ------------------ State changes ------------------

    def start_round(self, test_mode: bool):
        """ Start a round from the main menu """
        # Images not prepared yet on the menu are made now, not during play
        warmup.finish()
        TestMode.reset()
        TestMode.enabled = test_mode
        # Test mode starts with a safe, empty stage: spawn what you want from the panel
        self.level.auto_spawn = not test_mode
        if test_mode:
            TestMode.god_mode = True
            TestMode.show_hitboxes = True
            self.apply_god_mode()
        self.state = GameState.PLAYING
        self._round_frames = 0
        self.level.start()

    def _round_paused(self) -> bool:
        """ True on the pause menu, or in the settings opened from it """
        return self.state == GameState.PAUSED or (
            self.state == GameState.SETTINGS and self._settings_return_state == GameState.PAUSED)

    def _on_focus_lost(self):
        """ No sound while the game is in the background, on any screen
        (during a round the playing state also opens the pause menu)
        """
        pygame.mixer.music.pause()
        pygame.mixer.pause()

    def _on_focus_gained(self):
        # A paused round stays silent until RESUME
        if not self._round_paused():
            pygame.mixer.music.unpause()
            pygame.mixer.unpause()

    def pause(self):
        self.state = GameState.PAUSED
        self._frozen_valid = False
        self._stop_player_input()
        self.ui_pause.reset()
        # Pause the music and every sound effect channel
        pygame.mixer.music.pause()
        pygame.mixer.pause()

    def resume(self):
        self.state = GameState.PLAYING
        pygame.mixer.music.unpause()
        pygame.mixer.unpause()

    def restart(self):
        """ Start the same kind of round again (test mode stays on) """
        self._reset_world()
        if TestMode.enabled:
            self.apply_god_mode()
        self.state = GameState.PLAYING
        self._round_frames = 0
        self.level.start()
        pygame.mixer.music.unpause()

    def to_main_menu(self):
        self._reset_world()
        TestMode.reset()
        self.ui_intro.reset()
        self.state = GameState.INTRO
        self._play_intro_music()

    def open_settings(self):
        self._settings_return_state = self.state
        self.ui_settings.reset()
        self.state = GameState.SETTINGS
