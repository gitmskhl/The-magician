import pygame
from . import consts, animation, explosion, map, light
from abc import ABC, abstractmethod
import copy
import random

class PhysicsEntity(ABC):
    
    def __init__(self, app, pos, vel, map: map.Map, max_speed=8, surf=None):
        self.app = app
        self.pos = list(pos)
        self.vel = list(vel)
        self.max_speed = max_speed
        self.map = map
        self.surf = surf
        self.collisions = {'top': False, 'bottom': False, 'left': False, 'right': False}

    def _move_x(self):
        self.collisions['left'] = self.collisions['right'] = False
        self.pos[0] += self.vel[0]
        rect = self.get_rect()
        intersections = self.map.get_solid_intersections(rect)
        for tile_rect in intersections:
            # pygame.draw.rect(self.app.screen, (255, 255, 0), (tile_rect.x - self.map.camera_x, tile_rect.y - self.map.camera_y, *tile_rect.size), 2)
            if self.vel[0] > 0:
                self.collisions['right'] = True
                rect.right = tile_rect.left
            elif self.vel[0] < 0:
                self.collisions['left'] = True
                rect.left = tile_rect.right
            self.vel[0] = 0
        self.pos[0] = rect.left

    def _move_y(self):
        self.collisions['top'] = self.collisions['bottom'] = False
        self.vel[1] = min(self.vel[1] + consts.GRAVITY, self.max_speed)
        self.pos[1] += self.vel[1]
        rect = self.get_rect()
        intersections = self.map.get_solid_intersections(rect)
        for tile_rect in intersections:
            # pygame.draw.rect(self.app.screen, (255, 0, 0), (tile_rect.x - self.map.camera_x, tile_rect.y - self.map.camera_y, *tile_rect.size), 2)
            if self.vel[1] > 0:
                self.collisions['bottom'] = True
                rect.bottom = tile_rect.top
            elif self.vel[1] < 0:
                self.collisions['top'] = True
                rect.top = tile_rect.bottom
            self.vel[1] = 0
        self.pos[1] = rect.top

    def move(self):
        self._move_x()
        self._move_y()

    @abstractmethod
    def get_rect(self):
        pass

class Player(PhysicsEntity):
    def __init__(self, app, pos, vel, map: map.Map):
        super().__init__(app, pos, vel, map)
        self.scale = 1.2
        self.current_state = 'idle'
        self.last_state = None
        self.time_in_air = 0
        self.move = [False] * 4 # left right up down
        self.flip = False
        # jumps
        self.jumps = 0
        self.max_jumps = 1
        self.jumping = False
        # attack
        self.attacking = False
        self.attack_energy = 0
        self.attack_timer = 0
        self.attack_period = 0
        # hurt
        self.max_hp = self.hp = 100
        self.died = False
        self.dieing = 0
        self.hurting = 0
        # move or run
        self.running = False
        self.walk_speed = 3
        self.run_speed = 5
        # died
        self.died_time = 60 * 10 # the time when the character is rendering before it will be destroed

        # special animations
        base_dir = 'data/spritesheets/common'
        self.special_animations = {
            'death_stone': animation.JoinFilesAnimation(base_dir, 'Stone', frame_duration=12, scale=1, colorkey=(0,) * 3, repeat=False)
        }
        self.death_animation = 'dead'

        # callbacks
        self.callback_timer = 0
        self.callback = None

    def _join_animations(self):
        for k, v in self.special_animations.items():
            self.animations[k] = v

    def update(self):
        self.last_state = self.current_state
        self.attack_timer = max(0, self.attack_timer - 1)
        self.attack_energy = min(self.max_attack_energy, self.attack_energy + 1)
        self.hurting = max(0, self.hurting - 1)
        self.callback_timer = max(0, self.callback_timer - 1)
        if self.callback and self.callback_timer == 0:
            self.callback()
            self.callback = None

        if self.died:
            self.dieing += 1
            state = self.death_animation #'dead'
            self.vel[0] = 0
            self.move = [False] * 4
            super().move()
        elif self.attacking:
            state = f'attack_{self.attack_type}'
            if self.animations[state].finished:
                self.attacking = False
        elif self.hurting > 0:
            state = 'hurt'
            if self.animations['hurt'].finished:
                self.hurting = 0
        else:
            state = 'idle'
            self.vel[0] = (self.move[1] - self.move[0]) * (self.run_speed if self.running else self.walk_speed)
            super().move()
            if self.collisions['bottom']:
                self.jumps = 0
                self.jumping = False
                self.time_in_air = 0
            if self.vel[0] != 0:
                state = 'run' if self.running else 'walk'
            if self.vel[1] != 0:
                self.time_in_air += 1
            if self.time_in_air > 10 and self.vel[1] > 0:
                if 'falling' in self.animations:
                    state = 'falling'
            if self.jumping:
                state = 'jump'
        
        if self.current_state != state:
            self.current_state = state
            self.animations[self.current_state].reset()
        self.animations[self.current_state].update()
    
    def render(self, surf):
        if self.flip:
            width = self.animations[self.current_state].get_current_frame().get_width()
            x = self.pos[0] - (width - self.base_rect.width)
        else:
            x = self.pos[0]
        y = self.pos[1] + self.base_rect.height - self.animations[self.current_state].get_current_frame().get_height()
        self.animations[self.current_state].render(surf, (x - self.map.camera_x, y - self.map.camera_y), self.flip)

    def get_rect(self):
        rect = self.base_rect.copy()
        rect.left = self.pos[0]
        rect.top = self.pos[1]
        return rect

    def jump(self):
        if self.jumps < self.max_jumps:
            self.jumps += 1
            self.vel[1] = -10
            self.jumping = True

    def attack(self):
        if self.attack_timer > 0: return
        if self.attacking or self.jumping or self.hurting > 0: return
        if self.attack_energy < self.attack_energies[self.attack_type]: return
        self.attack_energy -= self.attack_energies[self.attack_type]
        self.attacking = True
        self.attack_timer = self.attack_period
        self.attacks[self.attack_type](self)
    
    def hurt(self, damage=0):
        self.hurting = 30
        self.hp = max(0, self.hp - damage)
        if self.hp == 0:
            self.died = True

class MainPlayer(Player):
    def __init__(self, app, pos, vel, map: map.Map):
        super().__init__(app, pos, vel, map)
        # healthbar
        self.health_rect = pygame.Rect(10, 10, 120, 20)
        # energybar
        self.energy_rect = pygame.Rect(10, 40, 120, 20)
        
        
    def render(self, surf):
        super().render(surf)
        pygame.draw.rect(surf, (255, 0, 0), self.health_rect)
        pygame.draw.rect(surf, (0, 255, 0), (*self.health_rect.topleft, self.hp * self.health_rect.width / 100, self.health_rect.height))
        # energy
        pygame.draw.rect(surf, (255, 255, 255), self.energy_rect)
        coef = self.attack_energy / self.max_attack_energy
        red = 255 * (1 - coef)
        blue = 255 * coef
        pygame.draw.rect(surf, (red, 0, blue), (*self.energy_rect.topleft, self.energy_rect.width * coef, self.energy_rect.height))
        self.light_ball.render(surf, (self.map.camera_x, self.map.camera_y))

    def update(self):
        super().update()
        self.light_ball.update(self)

    def hurt(self, damage, delay, intensity):
        super().hurt(damage)
        self.map.shake_screen(delay=delay, intensity=intensity)


class NPC(Player):
    def __init__(self, app, pos, vel, map: map.Map, vision_radius=900, attack_distance=None):
        super().__init__(app, pos, vel, map)
        self.vision_area = pygame.Rect(0, 0, vision_radius, map.tile_size)
        self.attack_distance = attack_distance if attack_distance else map.tile_size
        self.fixed_enemy = None
        self.health_rect = pygame.Rect(0, 0, 50, 8)
        self.come = False
        
        self.near_distance = 400 + random.random() * 200
        self.panic_distance = self.near_distance + 100
        self.far_distance = 1000


    def search_enemy(self):
        newradius = 10 * self.vision_area.width
        self.last_vision_area = self.vision_area
        self.vision_area = pygame.Rect(self.vision_area.centerx - newradius, self.vision_area.y, 2 * newradius, self.vision_area.height * 10)

    def recover_vision_area(self):
        self.vision_area = self.last_vision_area


    def get_enemies(self):
        rect = self.get_vision_area()
        result = []
        for enemy in self.app.enemies:
            if not enemy.died and enemy.get_rect().colliderect(rect):
                result.append(enemy)
        return result

    def set_enemy_aim(self):
        if not self.fixed_enemy:
            enemies = self.get_enemies()
            if enemies:
                enemies = sorted(enemies, key=lambda x: abs(x.pos[0] - self.pos[0]))
                self.fixed_enemy = enemies[0]
        if self.fixed_enemy and self.fixed_enemy.died:
            self.fixed_enemy = None

    def get_vision_area(self):
        va = self.vision_area.copy()
        va.topleft = (self.get_rect().centerx - va.width // 2, self.pos[1])
        return va

    def get_inner_area(self):
        # ia = pygame.Rect(self.pos[0] - self.vision_area.width // 4, self.pos[1], self.vision_area.width // 2, self.vision_area.height)
        # return ia
        return self.get_vision_area()

    def is_cliff(self, deep=3, length=1):
        rect = self.get_rect()
        ahead_d = self.map.tile_size // 2
        y = (rect.bottom + ahead_d) // self.map.tile_size
        if self.flip:
            x = (self.pos[0] - ahead_d) // self.map.tile_size
            x_set = range(x - length + 1, x + 1)
        else:
            x = (rect.right + ahead_d) // self.map.tile_size
            x_set = range(x, x + length)

        return all([(x_, y_) not in self.map.tile_map for x_ in x_set for y_ in range(y, y + deep)])

    def follow_main_player(self, running=False):
        player_rect = self.app.main_player.get_rect()
        if abs(player_rect.x - self.pos[0]) < self.near_distance: 
            self.move = [False] * 4
            self.running = False
            return
        if abs(player_rect.x - self.pos[0]) > self.panic_distance:
            if player_rect.x < self.pos[0]:
                self.move[0] = True
                self.move[1] = False
                self.flip = True
                self.running = True if running else self.app.main_player.running
            else:
                self.move[0] = False
                self.move[1] = True
                self.flip = False
                self.running = True if running else self.app.main_player.running
        if self.collisions['left'] or self.collisions['right']:
            self.jump()

        if player_rect.top > self.pos[1] + 2 * self.map.tile_size: return
        cliff3 = self.is_cliff(length=3)
        if cliff3:
            self.move = [False] * 4
            self.running = False
        elif self.is_cliff(length=1):
            self.jump()


    def ai(self):
        if self.come:
            self.follow_main_player(running=True)
            return
        player_rect = self.app.main_player.get_rect()
        self.set_enemy_aim()
        if self.fixed_enemy:
            renemy = self.fixed_enemy.get_rect()
            rme = self.get_rect()
            if not renemy.colliderect(self.get_vision_area()):
                self.fixed_enemy = None
                return
            if renemy.right + self.attack_distance < rme.left:
                self.move[0] = True
                self.move[1] = False
                self.flip = True
            elif renemy.left - self.attack_distance > rme.right:
                self.move[0] = False
                self.move[1] = True
                self.flip = False
            else:
                if self.attacking: return
                self.flip = self.fixed_enemy.pos[0] < self.pos[0]
                self.attack()
        else:
            if abs(self.pos[0] - player_rect.x) > self.far_distance:
                self.move = [False] * 4
                self.running = False
                return
            else:
                self.follow_main_player()
        if self.collisions['left'] or self.collisions['right']:
            self.jump()
        

    def render(self, surf):
        super().render(surf)
        r = self.get_rect()
        self.health_rect.topleft = (r.centerx - self.health_rect.width // 2 - self.map.camera_x, r.top - self.health_rect.height - 5 - self.map.camera_y)
        pygame.draw.rect(surf, (255, 0, 0), self.health_rect)
        x = self.hp * self.health_rect.width / self.max_hp
        pygame.draw.rect(surf, (0, 255, 0), (*self.health_rect.topleft, x, self.health_rect.height))


class Wizard(MainPlayer):
    def __init__(self, app, pos, vel, map: map.Map):
        super().__init__(app, pos, vel, map)
        base_dir = 'data/spritesheets/entities/Wizard'
        self.animations = {
            'idle': animation.Animation(base_dir, 'Idle.png', 6, frame_duration=10, scale=self.scale, colorkey=(0,) * 3),
            'walk': animation.Animation(base_dir, 'Walk.png', 7, frame_duration=7, scale=self.scale, colorkey=(0,) * 3),
            'run':  animation.Animation(base_dir, 'Run.png', 8, frame_duration=7, scale=self.scale, colorkey=(0,) * 3),
            'jump':animation.Animation(base_dir, 'Jump.png', 11, frame_duration=5, scale=self.scale, colorkey=(0,) * 3, repeat=False),
            'attack_3':animation.Animation(base_dir, 'Attack_1.png', 10, frame_duration=3, scale=self.scale, colorkey=(0,) * 3),
            'attack_2':animation.Animation(base_dir, 'Attack_2.png', 4, frame_duration=4, scale=self.scale, colorkey=(0,) * 3),
            'attack_1':animation.Animation(base_dir, 'Attack_3.png', 7, frame_duration=4, scale=self.scale, colorkey=(0,) * 3),
            'hurt':animation.Animation(base_dir, 'Hurt.png', 4, frame_duration=10, scale=self.scale, colorkey=(0,) * 3),
            'dead':animation.Animation(base_dir, 'Dead.png', 4, frame_duration=25, scale=self.scale, colorkey=(0,) * 3, repeat=False),
            'falling': animation.Animation(base_dir, 'Jump.png', 11, frame_duration=0, scale=self.scale, colorkey=(0,) * 3, repeat=False),
        }
        self._join_animations()
        self.base_rect = self.animations['idle'].get_current_frame().get_rect()
        # attack
        self.attacks = [
            None,
            Wizard.attack_1,
            Wizard.attack_2,
            Wizard.attack_3
        ]
        self.attack_type = 1
        self.attack_energies = [None, 60 * 2, 60 * 8, 60 * 30]
        self.max_attack_energy = max(self.attack_energies[1:])
        self.attack_energy = self.max_attack_energy
        # explosions
        self.explosion_factory = explosion.ExplosionFactory((map.tile_size, map.tile_size))

        # lightning
        self.light_ball = light.LightBall(self)


    def attack_3(self):
        speedy = 0
        r = self.get_rect()
        efrect = self.app.explosion_factory.base_explosions['lightning 1'].get_rect()
        spawny = r.bottom - efrect.height + 5
        spawnx = r.right + r.width * 4
        if self.flip:
            spawnx = r.left - r.width * 4 - efrect.width
        expl = self.explosion_factory.make_explosion('lightning 1', (spawnx ,spawny), [0, speedy])
        self.app.finishing_effects.append(expl)
        # self.app.rigid_effects.append(expl)

    def attack_2(self):
        speedx = 10
        r = self.get_rect()
        if not self.flip:
            spawnx = r.right
        else:
            speedx = -speedx
            spawnx = r.left - r.width * 1.5
        spawny = (r.centery + r.y) // 2
        expl = self.explosion_factory.make_explosion('wizard attack 1', (spawnx ,spawny), [speedx, 0])
        self.app.rigid_effects.append(expl)

    def attack_1(self):
        attack_width = self.animations['attack_1']._max_width
        if self.flip:
            attack_area = pygame.Rect(self.pos[0] - attack_width, self.pos[1], attack_width, self.base_rect.height)
        else:
            attack_area = pygame.Rect(self.pos[0] + self.base_rect.width, self.pos[1], attack_width, self.base_rect.height)
        self.app.attack(attack_area, 20, attack_main_player=False, attack_enemies=True)



class Swordsman(NPC):
    def __init__(self, app, pos, vel, map: map.Map):
        super().__init__(app, pos, vel, map, vision_radius=800, attack_distance=50)
        base_dir = 'data/spritesheets/entities/Swordsman'
        self.animations = {
            'idle': animation.Animation(base_dir, 'Idle.png', 8, frame_duration=10, scale=self.scale, colorkey=(0,) * 3),
            'walk': animation.Animation(base_dir, 'Walk.png', 8, frame_duration=7, scale=self.scale, colorkey=(0,) * 3),
            'run':  animation.Animation(base_dir, 'Run.png', 8, frame_duration=7, scale=self.scale, colorkey=(0,) * 3),
            'jump':animation.Animation(base_dir, 'Jump.png', 8, frame_duration=5, scale=self.scale, colorkey=(0,) * 3, repeat=False),
            'hurt': animation.Animation(base_dir, 'Hurt.png', 3, frame_duration=10, scale=self.scale, colorkey=(0,) * 3),
            'dead': animation.Animation(base_dir, 'Dead.png', 3, frame_duration=25, scale=self.scale, colorkey=(0,) * 3, repeat=False),
            'falling': animation.Animation(base_dir, 'Jump.png', 8, frame_duration=0, scale=self.scale, colorkey=(0,) * 3, repeat=False),
            'attack_3':animation.Animation(base_dir, 'Attack_1.png', 6, frame_duration=4, scale=self.scale, colorkey=(0,) * 3),
            'attack_2':animation.Animation(base_dir, 'Attack_2.png', 3, frame_duration=5, scale=self.scale, colorkey=(0,) * 3),
            'attack_1':animation.Animation(base_dir, 'Attack_3.png', 4, frame_duration=4, scale=self.scale, colorkey=(0,) * 3),
        }
        self._join_animations()
        self.base_rect = self.animations['idle'].get_current_frame().get_rect()
        # attack
        self.attacks = [
            None,
            Swordsman.attack_1,
            Swordsman.attack_2,
            Swordsman.attack_3
        ]
        self.attack_type = 1
        self.attack_energies = [None, 60 * 1, 60 * 8, 60 * 30]
        self.max_attack_energy = max(self.attack_energies[1:])
        self.attack_energy = self.max_attack_energy
        self.attack_period = 40
        # explosions
        self.explosion_factory = explosion.ExplosionFactory((map.tile_size, map.tile_size))


    def attack_1(self, damage=20):
        attack_width = self.animations['attack_1']._max_width
        if self.flip:
            attack_area = pygame.Rect(self.pos[0] - attack_width, self.pos[1], attack_width, self.base_rect.height)
        else:
            attack_area = pygame.Rect(self.pos[0] + self.base_rect.width, self.pos[1], attack_width, self.base_rect.height)
        self.app.attack(attack_area, damage, attack_main_player=False, attack_enemies=True)

    def attack_2(self):
        self.attack_1(damage=40)

    def attack_3(self):
        self.attack_1(damage=100)
        


class Archer(NPC):
    def __init__(self, app, pos, vel, map: map.Map):
        super().__init__(app, pos, vel, map, vision_radius=900, attack_distance=900)
        base_dir = 'data/spritesheets/entities/Archer'
        attack_anim = animation.Animation(base_dir, 'Attack_1.png', 4, frame_duration=6, scale=self.scale, colorkey=(0,) * 3)
        self.animations = {
            'idle': animation.Animation(base_dir, 'Idle.png', 6, frame_duration=8, scale=self.scale, colorkey=(0,) * 3),
            'walk': animation.Animation(base_dir, 'Walk.png', 8, frame_duration=5, scale=self.scale, colorkey=(0,) * 3),
            'run':  animation.Animation(base_dir, 'Run.png', 8, frame_duration=7, scale=self.scale, colorkey=(0,) * 3),
            'jump':animation.Animation(base_dir, 'Jump.png', 9, frame_duration=5, scale=self.scale, colorkey=(0,) * 3, repeat=False),
            'hurt':animation.Animation(base_dir, 'Hurt.png', 3, frame_duration=10, scale=self.scale, colorkey=(0,) * 3),
            'dead':animation.Animation(base_dir, 'Dead.png', 3, frame_duration=25, scale=self.scale, colorkey=(0,) * 3, repeat=False),
            'falling': animation.Animation(base_dir, 'Jump.png', 9, frame_duration=0, scale=self.scale, colorkey=(0,) * 3, repeat=False),
            'attack_3': attack_anim,
            'attack_2': attack_anim,
            'attack_1': attack_anim
        }
        self._join_animations()
        self.base_rect = self.animations['idle'].get_current_frame().get_rect()
        # attack
        self.attacks = [
            None,
            Archer.attack_1,
            Archer.attack_1,
            Archer.attack_1
        ]
        self.attack_type = 1
        self.attack_energies = [None, ] + [60 * 1] * 3
        self.max_attack_energy = max(self.attack_energies[1:])
        self.attack_energy = self.max_attack_energy
        # explosions
        self.explosion_factory = explosion.ExplosionFactory((map.tile_size, map.tile_size))


    def attack_1(self):
        speedx = 10
        r = self.get_rect()
        if not self.flip:
            spawnx = r.right
        else:
            speedx = -speedx
            spawnx = r.left - r.width * 1.5
        spawny = (r.centery + r.y) // 2
        expl = self.explosion_factory.make_explosion('arrow', (spawnx ,spawny), [speedx, 0])
        self.app.rigid_effects.append(expl)

class EntityFactory:
    def __init__(self, app, map: map.Map):
        self.players = {
            'wizard': Wizard(app, [0, 0], [0, 0], map),
            'swordsman': Swordsman(app, [0, 0], [0, 0], map),
            'archer': Archer(app, [0, 0], [0, 0], map)
        }

    def make_player(self, player_name, pos, vel):
        player = copy.copy(self.players[player_name])
        player.animations = {k: copy.copy(v) for k, v in player.animations.items()}
        player.move = list(player.move)
        player.pos = list(pos)
        player.vel = list(vel)
        return player