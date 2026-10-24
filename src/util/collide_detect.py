from pygame import Rect


def hit_rect(sprite, ratio=1.0) -> Rect:
    """ Area of a sprite used for collisions:
    its fixed `hitbox` if it has one, else its rect scaled by `ratio` (centered)
    """
    hitbox = getattr(sprite, "hitbox", None)
    if hitbox is not None:
        return hitbox
    rect = sprite.rect
    scaled = Rect(0, 0, int(rect.width * ratio), int(rect.height * ratio))
    scaled.center = rect.center
    return scaled


def collide_detect(ratio=0.8):
    """ Collision function for pygame.sprite.spritecollide*, see `hit_rect` """
    def collide_func(a, b):
        return hit_rect(a, ratio).colliderect(hit_rect(b, ratio))
    return collide_func
