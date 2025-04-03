from scripts.entity import Player
from . import animation, explosion, map, utils
import copy
import pygame
import random


class NPC(Player):
    def __init__(self, app, pos, vel):
        super().__init__(app, pos, vel)
        self.va_width = self.app.map.tile_size
        self.va_height = self.app.map.tile_size
        self.walking = 0
        self.explosion_factory = explosion.ExplosionFactory((app.map.tile_size, app.map.tile_size))
        # healthbar
        self.health_rect = pygame.Rect(0, 0, 50, 8)
        self.fixed_enemy = None


    def render(self, surf):
        super().render(surf)
        r = self.get_rect()
        self.health_rect.topleft = (r.centerx - self.health_rect.width // 2 - self.app.map.camera_x, r.top - self.health_rect.height - 5 - self.app.map.camera_y)
        pygame.draw.rect(surf, (255, 0, 0), self.health_rect)
        x = self.hp * self.health_rect.width / self.max_hp
        pygame.draw.rect(surf, (0, 255, 0), (*self.health_rect.topleft, x, self.health_rect.height))
        

    def get_vision_area(self):
        if self.flip:
            va = pygame.Rect(self.pos[0] - self.va_width, self.pos[1], self.va_width, self.va_height)
        else:
            va = pygame.Rect(self.pos[0] + self.base_rect.width, self.pos[1], self.va_width, self.va_height)
        return va

    def get_enemies(self):
        enemies = []
        va = self.get_vision_area()
        if not self.app.main_player.died and va.colliderect(self.app.main_player.get_rect()): enemies.append(self.app.main_player)
        for npc in self.app.npcs:
            if not npc.died and va.colliderect(npc.get_rect()):
                enemies.append(npc)
        return enemies
    
    def set_aim(self):
        if self.fixed_enemy and self.fixed_enemy.died:
            self.fixed_enemy = None
        if not self.fixed_enemy:
            enemies = self.get_enemies()
            if not enemies: return
            enemies = sorted(enemies, key=lambda x: abs(x.pos[0] - self.pos[0]))
            self.fixed_enemy = enemies[0]

    def is_cliff(self, deep=3, length=1):
        rect = self.get_rect()
        ahead_d = self.app.map.tile_size // 2
        y = (rect.bottom + ahead_d) // self.app.map.tile_size
        if self.flip:
            x = (self.pos[0] - ahead_d) // self.app.map.tile_size
            x_set = range(x - length + 1, x + 1)
        else:
            x = (rect.right + ahead_d) // self.app.map.tile_size
            x_set = range(x, x + length)

        return all([(x_, y_) not in self.app.map.tile_map for x_ in x_set for y_ in range(y, y + deep)])

    def ai(self):
        super().update()
        if self.died: return
        self.walking = max(0, self.walking - 1)
        self.set_aim()
        if self.fixed_enemy and self.get_vision_area().colliderect(self.fixed_enemy.get_rect()):
            self.attack()
        if self.attacking: 
            self.walking = 0
            self.move = [False] * 4
            return
        if self.walking > 0:
            if self.collisions['left'] or self.collisions['right']:
                self.flip = not self.flip
            elif self.is_cliff(deep=1, length=1):
                self.flip = not self.flip
            self.move[0] = self.flip
            self.move[1] = not self.flip
        elif random.random() < .01:
            self.walking = 90
        else:
            self.move[0] = self.move[1] = False


class Demon(NPC):
    def __init__(self, app, pos, vel):
        super().__init__(app, pos, vel)
        self.max_hp = self.hp = 200
        self.scale=1
        self.va_width = 70
        base_dir = 'data/spritesheets/enemies/demon'
        self.animations = {
            'idle': animation.JoinFilesAnimation(base_dir, 'Idle', frame_duration=15, scale=self.scale, colorkey=(0,) * 3),
            'walk': animation.JoinFilesAnimation(base_dir, 'Walk', frame_duration=7, scale=self.scale, colorkey=(0,) * 3),
            'attack_1': animation.JoinFilesAnimation(base_dir, 'Attack', frame_duration=7, scale=self.scale, colorkey=(0,) * 3),
            'hurt': animation.JoinFilesAnimation(base_dir, 'Hurt', frame_duration=7, scale=self.scale, colorkey=(0,) * 3, repeat=False),
            'dead': animation.JoinFilesAnimation(base_dir, 'Death', frame_duration=10, scale=self.scale, colorkey=(0,) * 3, repeat=False),
        }
        self.base_rect = self.animations['idle'].get_current_frame().get_rect()
        # attack
        self.attacks = [
            None,
            Demon.attack_1,
        ]
        self.attack_type = 1
        self.attack_energies = [None, 60 * 1]
        self.max_attack_energy = max(self.attack_energies[1:])

    def attack_1(self):
        img = self.animations['attack_1'].frames[0]
        width, height = img.get_width(), img.get_height()
        x = self.pos[0]
        y = self.pos[1] + self.base_rect.height - height
        if self.flip:
            x = self.pos[0] + self.base_rect.width - width
        attack_rect = pygame.Rect(x, y, width, height)
        self.app.attack(attack_rect, 20, attack_main_player=True, attack_enemies=False, delay=50, intensity=100)
        # return attack_rect
    

class Dragon(NPC):
    def __init__(self, app, pos, vel):
        super().__init__(app, pos, vel)
        self.max_hp = self.hp = 500
        self.scale=1.2
        self.va_width = 110
        base_dir = 'data/spritesheets/enemies/dragon'
        self.animations = {
            'idle': animation.JoinFilesAnimation(base_dir, 'Idle', frame_duration=30, scale=self.scale, colorkey=(0,) * 3),
            'walk': animation.JoinFilesAnimation(base_dir, 'Walk', frame_duration=15, scale=self.scale, colorkey=(0,) * 3),
            'attack_1': animation.JoinFilesAnimation(base_dir, 'Attack', frame_duration=15, scale=self.scale, colorkey=(0,) * 3),
            'hurt': animation.JoinFilesAnimation(base_dir, 'Hurt', frame_duration=7, scale=self.scale, colorkey=(0,) * 3, repeat=False),
            'dead': animation.JoinFilesAnimation(base_dir, 'Death', frame_duration=10, scale=self.scale, colorkey=(0,) * 3, repeat=False),
        }
        self.base_rect = self.animations['idle'].get_current_frame().get_rect()
        # attack
        self.attacks = [
            None,
            Dragon.attack_1,
        ]
        self.attack_energies = [None, 60 * 3]
        self.max_attack_energy = max(self.attack_energies[1:])
        self.attack_type = 1

    def attack_1(self):
        erect = self.explosion_factory.base_explosions['dragon_fire'].animation.frames[2].get_rect()
        if self.flip:
            x = self.pos[0] - erect.width
        else:
            x = self.pos[0] + self.base_rect.width
        y = self.pos[1]
        erect.topleft = (x, y)
        fire_attack_expl = self.explosion_factory.make_explosion('dragon_fire', erect.topleft, (0, 0), 30, self.flip)
        self.app.finishing_effects.append(fire_attack_expl)
        self.app.attack(erect, 50, attack_main_player=True, attack_enemies=False, delay=50, intensity=140)


class Jinn(NPC):
    def __init__(self, app, pos, vel):
        super().__init__(app, pos, vel)
        self.max_hp = self.hp = 120
        self.scale=1
        self.va_width = 200
        base_dir = 'data/spritesheets/enemies/jinn_animation'
        self.animations = {
            'idle': animation.JoinFilesAnimation(base_dir, 'Idle', frame_duration=14, scale=self.scale, colorkey=(0,) * 3),
            'walk': animation.JoinFilesAnimation(base_dir, 'Flight', frame_duration=7, scale=self.scale, colorkey=(0,) * 3),
            'attack_1': animation.JoinFilesAnimation(base_dir, 'Attack', frame_duration=15, scale=self.scale, colorkey=(0,) * 3),
            'hurt': animation.JoinFilesAnimation(base_dir, 'Hurt', frame_duration=7, scale=self.scale, colorkey=(0,) * 3, repeat=False),
            'dead': animation.JoinFilesAnimation(base_dir, 'Death', frame_duration=10, scale=self.scale, colorkey=(0,) * 3, repeat=False),
        }
        self.base_rect = self.animations['idle'].get_current_frame().get_rect()
        # attack
        self.attacks = [
            None,
            Jinn.attack_1,
        ]
        self.attack_energies = [None, 60 * 6]
        self.max_attack_energy = max(self.attack_energies[1:])
        self.attack_type = 1
        # died time
        self.died_time = 60 * 1

    def attack_1(self):
        speed = 3
        ball = self.explosion_factory.base_explosions['jinn_ball'].get_rect()
        y = self.get_rect().centery
        if self.flip:
            x = self.pos[0] - ball.width
            speed = -speed
        else:
            x = self.pos[0] + self.base_rect.width
        fball_expl = self.explosion_factory.make_explosion('jinn_ball', (x, y), (speed, 0), 30, self.flip)
        self.app.finishing_effects.append(fball_expl)

class Lizard(NPC):
    def __init__(self, app, pos, vel):
        super().__init__(app, pos, vel)
        self.max_hp = self.hp = 100
        self.scale=1.3
        self.va_width = 70
        base_dir = 'data/spritesheets/enemies/lizard'
        self.animations = {
            'idle': animation.JoinFilesAnimation(base_dir, 'Idle', frame_duration=14, scale=self.scale, colorkey=(0,) * 3),
            'walk': animation.JoinFilesAnimation(base_dir, 'Walk', frame_duration=7, scale=self.scale, colorkey=(0,) * 3),
            'attack_1': animation.JoinFilesAnimation(base_dir, 'Attack', frame_duration=15, scale=self.scale, colorkey=(0,) * 3),
            'hurt': animation.JoinFilesAnimation(base_dir, 'Hurt', frame_duration=7, scale=self.scale, colorkey=(0,) * 3, repeat=False),
            'dead': animation.JoinFilesAnimation(base_dir, 'Death', frame_duration=10, scale=self.scale, colorkey=(0,) * 3, repeat=False),
        }
        self.base_rect = self.animations['idle'].get_current_frame().get_rect()
        # attack
        self.attacks = [
            None,
            Lizard.attack_1,
        ]
        self.attack_energies = [None, 60 * 3]
        self.max_attack_energy = max(self.attack_energies[1:])
        self.attack_type = 1

    def attack_1(self):
        img = self.animations['attack_1'].frames[0]
        width, height = img.get_width(), img.get_height()
        x = self.pos[0]
        y = self.pos[1] + self.base_rect.height - height
        if self.flip:
            x = self.pos[0] + self.base_rect.width - width
        attack_rect = pygame.Rect(x, y, width, height)
        self.app.attack(attack_rect, 20, attack_main_player=True, attack_enemies=False, delay=50, intensity=60)


class Medusa(NPC):
    def __init__(self, app, pos, vel):
        super().__init__(app, pos, vel)
        self.max_hp = self.hp = 100
        self.scale=1.3
        self.va_width = 70
        base_dir = 'data/spritesheets/enemies/medusa'
        self.animations = {
            'idle': animation.JoinFilesAnimation(base_dir, 'Idle', frame_duration=14, scale=self.scale, colorkey=(0,) * 3),
            'walk': animation.JoinFilesAnimation(base_dir, 'Walk', frame_duration=7, scale=self.scale, colorkey=(0,) * 3),
            'attack_1': animation.JoinFilesAnimation(base_dir, 'Attack', frame_duration=10, scale=self.scale, colorkey=(0,) * 3),
            'hurt': animation.JoinFilesAnimation(base_dir, 'Hurt', frame_duration=7, scale=self.scale, colorkey=(0,) * 3, repeat=False),
            'dead': animation.JoinFilesAnimation(base_dir, 'Death', frame_duration=10, scale=self.scale, colorkey=(0,) * 3, repeat=False),
        }
        self.base_rect = self.animations['idle'].get_current_frame().get_rect()
        # attack
        self.attacks = [
            None,
            Medusa.attack_1,
        ]
        self.attack_energies = [None, 60 * 3]
        self.max_attack_energy = max(self.attack_energies[1:])
        self.attack_type = 1

    def attack_1(self):
        def real_attack():
            img = self.animations['attack_1'].frames[4]
            width, height = img.get_width(), img.get_height()
            x = self.pos[0]
            y = self.pos[1] + self.base_rect.height - height
            if self.flip:
                x = self.pos[0] + self.base_rect.width - width
            attack_rect = pygame.Rect(x, y, width, height)
            self.app.attack(attack_rect, 70, attack_main_player=True, attack_enemies=False, delay=50, intensity=150)
            if self.app.main_player.died:
                self.app.main_player.death_animation = 'death_stone'
        self.callback = real_attack
        self.callback_timer = self.animations['attack_1'].frame_duration * 3

class SmallDragon(Dragon):
    def __init__(self, app, pos, vel):
        super().__init__(app, pos, vel)
        self.max_hp = self.hp = 60
        base_dir = 'data/spritesheets/enemies/small_dragon'
        self.animations = {
            'idle': animation.JoinFilesAnimation(base_dir, 'Idle', frame_duration=14, scale=self.scale, colorkey=(0,) * 3),
            'walk': animation.JoinFilesAnimation(base_dir, 'Walk', frame_duration=7, scale=self.scale, colorkey=(0,) * 3),
            'attack_1': animation.JoinFilesAnimation(base_dir, 'Attack', frame_duration=10, scale=self.scale, colorkey=(0,) * 3),
            'hurt': animation.JoinFilesAnimation(base_dir, 'Hurt', frame_duration=7, scale=self.scale, colorkey=(0,) * 3, repeat=False),
            'dead': animation.JoinFilesAnimation(base_dir, 'Death', frame_duration=10, scale=self.scale, colorkey=(0,) * 3, repeat=False),
        }
        self.base_rect = self.animations['idle'].get_current_frame().get_rect()
        # attack
        self.attacks = [
            None,
            SmallDragon.attack_1,
        ]

    def attack_1(self):
        speed = 0
        erect = self.explosion_factory.base_explosions['small_dragon_fire'].animation.frames[2].get_rect()
        if self.flip:
            speed = -speed
            x = self.pos[0] - erect.width
        else:
            x = self.pos[0] + self.base_rect.width
        y = self.pos[1]
        erect.topleft = (x, y)
        fire_attack_expl = self.explosion_factory.make_explosion('small_dragon_fire', erect.topleft, (speed, 0), 30, self.flip)
        self.app.finishing_effects.append(fire_attack_expl)
        self.app.attack(erect, 10, attack_main_player=True, attack_enemies=False, delay=30, intensity=40)
        


class EnemiesFactory:
    def __init__(self, app):
        self.enemies = {
            'demon': Demon(app, [0, 0], [0, 0]),
            'dragon': Dragon(app, [0, 0], [0, 0]),
            'jinn': Jinn(app, [0, 0], [0, 0]),
            'lizard': Lizard(app, [0, 0], [0, 0]),
            'medusa': Medusa(app, [0, 0], [0, 0]),
            'small_dragon': SmallDragon(app, [0, 0], [0, 0]),
        }

    def make_enemy(self, enemy_name, pos, vel):
        enemy = copy.copy(self.enemies[enemy_name])
        enemy.animations = {k: copy.copy(v) for k, v in enemy.animations.items()}
        enemy.move = list(enemy.move)
        enemy.pos = list(pos)
        enemy.vel = list(vel)
        return enemy