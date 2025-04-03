from scripts import utils, animation
import copy
import os
import pygame

class BaseExplosion:
    def __init__(self, pos, vel, animation, repeat_count=-1, damage=0, finish_explosion=None, flip=False):
        self.pos = list(pos)
        self.vel = list(vel)
        self.animation = animation
        self.repeat_count = repeat_count
        self.damage = damage
        self.finish_explosion = finish_explosion

        self.count = 0
        self.lock = False
        self.disable = False

        self.flip = flip

    def update(self):
        self.animation.update()
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        if not self.animation.finished:
            self.lock = False
        if self.animation.finished and not self.lock:
            self.lock = True
            self.count += 1
            if self.repeat_count != -1 and self.count == self.repeat_count:
                self.disable = True
    
    def render(self, surf, camera):
        if self.disable: return
        self.animation.render(surf, (self.pos[0] - camera[0], self.pos[1] - camera[1]), flip=self.flip)

    def get_rect(self):
        rect = self.animation.get_current_frame().get_rect()
        rect.topleft = tuple(self.pos)
        return rect

class DirsExplosion(BaseExplosion):
    def __init__(self, dirpath, frame_duration, pos, vel, scale, size=None, colorkey=None, repeat_count=1, damage=0, finish_explosion=None, bounding=False, flip=False):
        super().__init__(pos, vel, animation.ListOfFilesAnimation(dirpath, frame_duration, scale, True, colorkey, size, bounding), repeat_count, damage, finish_explosion=finish_explosion, flip=flip)
        
class CentroidDirsExplosion(DirsExplosion):
    def __init__(self, dirpath, frame_duration, pos, vel, scale, size=None, colorkey=None, repeat_count=1, damage=0, finish_explosion=None, bounding=True, flip=False):
        super().__init__(dirpath, frame_duration, pos, vel, scale, size, colorkey, repeat_count, damage, finish_explosion, bounding, flip)

    def render(self, surf, camera):
        if self.disable: return
        imrect = self.animation.get_current_frame().get_rect()
        self.animation.render(surf, (self.pos[0] - imrect.width // 2 - camera[0], self.pos[1] - imrect.height // 2 - camera[1]), flip=self.flip)

    def get_rect(self):
        rect = self.animation.get_current_frame().get_rect()
        rect.topleft = (self.pos[0] - rect.width // 2, self.pos[1] - rect.height // 2)
        return rect


def finish_explosion8_maker(explfactory, lightning, map):
    lrect = lightning.get_rect()
    explrect = explfactory.base_explosions['blue explosion 8'].get_rect()
    x = lrect.centerx - explrect.width // 2
    real_width = 4
    physical_lrect = pygame.Rect(lrect.centerx - real_width // 2, lrect.top, real_width, lrect.height)
    intersections = map.get_solid_intersections(physical_lrect)
    if not intersections: return None
    bottom = min([r.y for r in intersections]) if len(intersections) > 0 else lrect.bottom
    y = bottom - explrect.height + explrect.width // 3
    return explfactory.make_explosion('blue explosion 8', (x, y), (0, 0))

def finish_explosion1_maker(explfactory, ballexpl, map):
    center = ballexpl.get_rect().center
    explosion = explfactory.make_explosion('red explosion 1', [0, 0], [0, 0])
    rect = explosion.get_rect()
    rect.center = center
    explosion.pos = list(rect.topleft)
    return explosion

class ExplosionFactory:
    def __init__(self, size=None):
        base_dir = 'data/effects'
        self.base_explosions = {
            'wizard attack 1': DirsExplosion(
                os.path.join(base_dir, 'fireballs/ball1'),
                frame_duration=7,
                pos=[0, 0],
                vel=[0, 0],
                scale=1,
                size=(size[0] // 2, size[0] // 2),
                repeat_count=-1,
                damage=20,
                finish_explosion=lambda expl, map: finish_explosion1_maker(self, expl, map)
            ),
            'red explosion 1': DirsExplosion(
                os.path.join(base_dir, 'explosions/Explosion_1'),
                frame_duration=2,
                pos=[0, 0],
                vel=[0, 0],
                scale=1,
                size=(size[0] * 2, size[0] * 2),
                repeat_count=1
            ),
            'blue explosion 8': DirsExplosion(
                os.path.join(base_dir, 'explosions/Explosion_8'),
                frame_duration=3,
                pos=[0, 0],
                vel=[0, 0],
                scale=1,
                damage=80,
                size=(size[0] * 3, size[0] * 3),
                repeat_count=1
            ),
            'lightning 1': DirsExplosion(
                os.path.join(base_dir, 'explosions/Explosion_7/1'),
                frame_duration=5,
                pos=[0, 0],
                vel=[0, 0],
                scale=1,
                # size=(size[0] * 2, size[0] * 2),
                repeat_count=1,
                finish_explosion=lambda expl, map: finish_explosion8_maker(self, expl, map)
            ),
            'arrow': DirsExplosion(
                os.path.join(base_dir, 'fireballs/arrows'),
                frame_duration=100,
                pos=[0, 0],
                vel=[0, 0],
                scale=1,
                damage=20,
                size=(size[0] // 2, size[0] // 2),
                repeat_count=-1,
            ),
            'dragon_fire': DirsExplosion(
                os.path.join(base_dir, 'fireballs/dragon_fire'),
                frame_duration=10,
                pos=[0, 0],
                vel=[0, 0],
                scale=2,
                colorkey=(0, 0, 0),
                # size=(size[0] // 2, size[0] // 2),
                repeat_count=1,
                bounding=True
            ),
            'small_dragon_fire': DirsExplosion(
                os.path.join(base_dir, 'fireballs/small_dragon_fire'),
                frame_duration=10,
                pos=[0, 0],
                vel=[0, 0],
                scale=2,
                colorkey=(0, 0, 0),
                # size=(size[0] // 2, size[0] // 2),
                repeat_count=1,
                bounding=True
            ),
            'jinn_ball': CentroidDirsExplosion(
                os.path.join(base_dir, 'fireballs/jinn_ball'),
                frame_duration=8,
                pos=[0, 0],
                vel=[0, 0],
                scale=1,
                damage=30,
                colorkey=(0, 0, 0),
                # size=(size[0] * 1,) * 2,
                repeat_count=1,
                bounding=True
            ),
        }

    def make_explosion(self, explosion_name, pos, vel, damage=0, flip=False):
        explosion = copy.copy(self.base_explosions[explosion_name])
        explosion.pos = list(pos)
        explosion.vel = list(vel)
        explosion.flip = flip
        explosion.damage = damage if not hasattr(explosion, 'damage') else explosion.damage
        return explosion        
