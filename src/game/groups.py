from pygame.sprite import GroupSingle, Group, LayeredDirty

G_Player1 = GroupSingle(None)
G_Player2 = GroupSingle(None)
G_Players = Group()

G_Bomb = GroupSingle(None)

G_Enemys = Group()

G_BOSS = GroupSingle(None)

G_Player_Bullets = Group()
G_Enemy_Bullets = Group()

G_Plane = Group()
G_Destroyed_Plane = Group()

G_Shield = LayeredDirty()

G_Supplies = Group()

G_Effects = Group()
# Floating texts, drawn over the effects
G_Texts = Group()
