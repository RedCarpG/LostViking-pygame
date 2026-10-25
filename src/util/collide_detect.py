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


_collide_funcs = {}


def collide_detect(ratio=0.8):
    """ Collision function for pygame.sprite.spritecollide*, see `hit_rect` """
    func = _collide_funcs.get(ratio)
    if func is None:
        def func(a, b):
            # Quick test first: every hit area lies inside its sprite rect,
            # and most pairs are far apart
            if not a.rect.colliderect(b.rect):
                return False
            return hit_rect(a, ratio).colliderect(hit_rect(b, ratio))
        _collide_funcs[ratio] = func
    return func
