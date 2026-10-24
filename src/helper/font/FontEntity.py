from src.setting import COLOR


class FontEntity:
    def __init__(self, screen, font, text='', position=(0, 0), antialias=False, color=COLOR.WHITE, background=None):
        self.font = font
        self.antialias = antialias
        self.color = color
        self.background = background
        self.text = text
        self.screen = screen
        self.render = self.font.render(
            self.text, self.antialias, self.color, self.background)
        self.rect = self.render.get_rect()
        self.rect.move_ip(position)

    def blit(self):
        self.screen.blit(self.render, (self.rect[0], self.rect[1]))

    def move_center(self, center_position):
        self.rect.center = center_position

    def move(self, position):
        self.rect.move_ip(position)

    def change_text(self, text):
        self.text = text
        self.rendering()

    def change_font(self, font):
        self.font = font
        self.rendering()

    def change_color(self, color):
        self.color = color
        self.rendering()

    def rendering(self):
        self.render = self.font.render(
            self.text, self.antialias, self.color, self.background)
        self.rect = self.render.get_rect(center=self.rect.center)
