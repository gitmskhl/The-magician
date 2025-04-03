import pygame
import sys
from scripts import map, entity, explosion, enemy, coin, portal, transition, utils
from scripts.consts import window_size
import copy

pygame.init()

screen = pygame.display.set_mode(window_size, pygame.NOFRAME | pygame.HWSURFACE | pygame.DOUBLEBUF)

# light effects
darkness = pygame.Surface(window_size, pygame.SRCALPHA)
light_radius = 100
light_min_radius = 80
light_max_radius = 120
t = 0
t_speed = .1

class App:
    def __init__(self, restart=False):
        self.screen = screen
        self.clock = pygame.time.Clock()
        if not restart:
            self.map = map.Map()
            self.original_map = copy.copy(self.map)
            self.original_map.tile_map = copy.deepcopy(self.map.tile_map)
        else:
            self.map = copy.copy(self.original_map)
            self.map.tile_map = copy.deepcopy(self.original_map.tile_map)
        
        if not restart:
            self.entity_factory = entity.EntityFactory(self)
            self.enemies_factory = enemy.EnemiesFactory(self)
        else:
            self.enemies_factory
        
        # main player
        self.main_player = self.entity_factory.make_player('wizard', (self.map.camera_x, self.map.camera_y), [0, 0])
        self.main_player.surf = screen
        self.restart_timer = 0
        self.restart_timer_set = False
        # npc
        self.npcs = []
        for i, npc_name in enumerate(sorted(self.entity_factory.players.keys())):
            for pos, tile in self.map.get_tiles('npc', i):
                npc = self.entity_factory.make_player(npc_name, pos, (0, 0))
                self.npcs.append(npc)

        self.must_attack_enemy = False
        if not restart:
            self.attack_enemy_icon = utils.load_image("data/icons/swords_icon.png", 1, size=(50, 50))
        
        self.come_here = False
        if not restart:
            self.horn_icon = utils.load_image('data/icons/horn_icon.png', scale=1, size=(50, 50))
        
        # enemies
        self.enemies = []
        for i, enemy_name in enumerate(sorted(self.enemies_factory.enemies.keys())):
            for pos, tile in self.map.get_tiles('entities', i):
                demon = self.enemies_factory.make_enemy(enemy_name, pos, (0, 0))
                self.enemies.append(demon)
        
        # keys
        self.shift_pressed = False
        self.ctrl_pressed = False

        # explosions
        self.finishing_effects = []
        self.rigid_effects = []
        if not restart:
            self.explosion_factory = explosion.ExplosionFactory(size=(self.map.tile_size, ) *  2)

        # rigid bodies with effects
        self.rigidbodies = []
        self._init_coins()

        # portals
        self.portals = []

        # transitions
        self.transitions = {
            'expand': transition.IrisTransition(period=60, expand=True),
            'shrinking': transition.IrisTransition(period=40, expand=False),
        }
        self.current_transition = self.transitions['expand']

        # darkness
        self.start_level = self.map.camera_y
        self.dark_step = 50 
        self.dark_surf = pygame.Surface(window_size, pygame.SRCALPHA)
        self.light_on = False

    def _init_coins(self):
        coinClass = [coin.EnergyCoin, coin.HealthCoin]
        for variant, cclass in enumerate(coinClass):
            for pos, tile in self.map.get_tiles('coins', variant=variant, absolute=True, keep=False):
                c = cclass(pos, 10)
                self.rigidbodies.append(c)
            for pos, tile in self.map.get_offgrid_tiles('coins', variant=variant, keep=False):
                c = cclass((pos[0] * self.map.k, pos[1] * self.map.k), 10)
                self.rigidbodies.append(c) 

    def attack(self, rect, damage, attack_main_player=True, attack_enemies=True, attack_npc=True, delay=60, intensity=80):
        def fattack_main_player(rect, damage):
            if self.main_player.get_rect().colliderect(rect):
                self.main_player.hurt(damage, delay=delay, intensity=intensity)
                return True
            return False
        def fattack_enemies(rect, damage):
            for enemy in self.enemies:
                if not enemy.died and enemy.get_rect().colliderect(rect):
                    enemy.hurt(damage)
                    return True
            return False
        def fattack_npc(rect, damage):
            for npc in self.npcs:
                if not npc.died and npc.get_rect().colliderect(rect):
                    npc.hurt(damage)
                    return True
            return False
    
        collision = False
        if attack_main_player:
            collision = fattack_main_player(rect, damage) or collision
        if attack_enemies:
            collision = fattack_enemies(rect, damage) or collision
        if attack_npc:
            collision = fattack_npc(rect, damage) or collision
        return collision
            
        
    def make_dark(self):
        delta_level = max(0, self.map.camera_y - self.start_level) / self.dark_step#/ self.map.tile_size
        transparency = min(255, delta_level)
        self.dark_surf.fill((0, 0, 0, transparency))
        if self.light_on:
            center = self.main_player.get_rect().center
            light_radius = int(transparency)
            for r in range(light_radius, 0, -1):
                pygame.draw.circle(self.dark_surf, (0, 0, 0, r), (center[0] - self.map.camera_x, center[1] - self.map.camera_y), r)
        screen.blit(self.dark_surf, (0, 0))


    def run(self):
        running = True

        while running:

            self.clock.tick(60)

            self.map.camera_x += (self.main_player.pos[0] - window_size[0] // 2 - self.map.camera_x) // 30
            self.map.camera_y += (self.main_player.pos[1] - window_size[1] // 2 - self.map.camera_y) // 30
            self.map.update()
            self.map.render(screen)

            # npc
            for npc in self.npcs:
                npc.ai()
                npc.update()
                if npc.died and npc.dieing > npc.died_time:
                    self.npcs.remove(npc)
                rect = npc.get_rect() 
                if not (
                    rect.right - self.map.camera_x < 0
                    or rect.left - self.map.camera_x > window_size[0]
                    or rect.bottom - self.map.camera_y < 0
                    or rect.top - self.map.camera_y > window_size[1]
                ): npc.render(screen)

            # enemies
            for enemy in self.enemies:
                enemy.ai()
                # enemy.update()
                rect = enemy.get_rect() 
                if enemy.died and enemy.dieing > enemy.died_time:
                    self.enemies.remove(enemy)
                if not (
                    rect.right - self.map.camera_x < 0
                    or rect.left - self.map.camera_x > window_size[0]
                    or rect.bottom - self.map.camera_y < 0
                    or rect.top - self.map.camera_y > window_size[1]
                ): enemy.render(screen)

            if self.light_on:
                self.make_dark()
                

            # main player
            self.main_player.update()
            self.main_player.render(screen)         



            if not self.light_on:
                self.make_dark()

            self.main_player.render_bars(screen)

            # portals
            for port in self.portals:
                port.update()
                port.render(screen, (self.map.camera_x, self.map.camera_y))
            

            if self.main_player.died:
                if not self.restart_timer_set:
                    self.restart_timer = 60 * 5
                    self.restart_timer_set = True
                self.restart_timer = max(0, self.restart_timer - 1)
                if self.restart_timer == 40:
                    self.current_transition = self.transitions['shrinking']
                    self.current_transition.reset()
                if self.restart_timer == 0 and not self.current_transition:
                    self.__init__(restart=True)
                    continue
                
            # self.main_player.light_ball.render(screen, (self.map.camera_x, self.map.camera_y))

            for rb in self.rigidbodies:
                rect = rb.get_rect()
                if (
                    rect.right - self.map.camera_x < 0
                    or rect.left - self.map.camera_x > window_size[0]
                    or rect.bottom - self.map.camera_y < 0
                    or rect.top - self.map.camera_y > window_size[1]
                ): continue
                rb.update(self)
                rb.render(screen, (self.map.camera_x, self.map.camera_y))

            # explosions
            for explosion in self.finishing_effects:
                explosion.update()
                explosion.render(screen, (self.map.camera_x, self.map.camera_y))
                collision = False
                if explosion.damage != 0:
                    collision = self.attack(explosion.get_rect(), explosion.damage, attack_main_player=True, attack_enemies=False)
                if collision:
                    explosion.damage = 0
                if explosion.disable:
                    self.finishing_effects.remove(explosion)
                    if explosion.finish_explosion:
                        expl = explosion.finish_explosion(explosion, self.map)
                        if expl:
                            self.finishing_effects.append(expl)


            ## rigid
            for effect in self.rigid_effects:
                effect.update()
                effect.render(screen, (self.map.camera_x, self.map.camera_y))
                collision = False
                if effect.damage != 0:
                    collision = self.attack(effect.get_rect(), effect.damage, attack_main_player=True, attack_enemies=True)
                if self.map.get_solid_intersections(effect.get_rect()) or collision:
                    self.rigid_effects.remove(effect)
                    if effect.finish_explosion:
                        expl = effect.finish_explosion(effect, self.map)
                        self.finishing_effects.append(expl)


            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_LEFT and not self.main_player.died:
                        self.main_player.move[0] = True
                        self.main_player.flip = True
                    elif event.key == pygame.K_RIGHT and not self.main_player.died:
                        self.main_player.move[1] = True
                        self.main_player.flip = False
                    elif event.key == pygame.K_SPACE and not self.main_player.died:
                        self.main_player.jump()
                    elif event.key == pygame.K_x and not self.main_player.died:
                        if self.main_player.attacking: continue
                        self.main_player.attack_type = 2 if self.ctrl_pressed else 1
                        if self.shift_pressed:
                            self.main_player.attack_type = 3
                        self.main_player.attack()
                    elif event.key == pygame.K_LSHIFT:
                        self.main_player.running = True
                        self.shift_pressed = True
                    elif event.key == pygame.K_LCTRL:
                        self.ctrl_pressed = True
                    elif event.key == pygame.K_c:
                        if self.main_player.attack_energy == self.main_player.max_attack_energy:
                            center = self.main_player.get_rect().center
                            port = portal.Portal(center, 40)
                            self.portals = [port]
                            self.main_player.attack_energy = 0
                    elif event.key == pygame.K_z and not self.main_player.died:
                        if self.portals and self.main_player.attack_energy > self.main_player.max_attack_energy // 3:
                            p = self.portals[0]
                            self.main_player.pos = [p.center[0] - p.r, p.center[1] - p.r]
                            self.main_player.attack_energy -= self.main_player.max_attack_energy // 3
                    elif event.key == pygame.K_r and not self.come_here:
                        if self.must_attack_enemy:
                            for npc in self.npcs: npc.recover_vision_area()
                        else:
                            for npc in self.npcs: npc.search_enemy()
                        self.must_attack_enemy = not self.must_attack_enemy
                    elif event.key == pygame.K_q:
                        self.come_here = not self.come_here
                        if self.come_here:
                            for npc in self.npcs: 
                                npc.come = True
                                npc.search_enemy()
                        else:
                            for npc in self.npcs: 
                                npc.come = False
                                npc.recover_vision_area()
                    elif event.key == pygame.K_l:
                        self.light_on = not self.light_on
                        self.main_player.light_ball.reset()
                
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.main_player.move[0] = False
                    elif event.key == pygame.K_RIGHT:
                        self.main_player.move[1] = False
                    elif event.key == pygame.K_LSHIFT:
                        self.main_player.running = False
                        self.shift_pressed = False
                    elif event.key == pygame.K_LCTRL:
                        self.ctrl_pressed = False

            if self.come_here:
                screen.blit(self.horn_icon, (window_size[0] - self.horn_icon.get_width() - 10, 5))
            elif self.must_attack_enemy:
                screen.blit(self.attack_enemy_icon, (window_size[0] - self.attack_enemy_icon.get_width() - 10, 5))

            # transitions
            if self.current_transition:
                self.current_transition.update()
                self.current_transition.render(screen)
                if self.current_transition.finished:
                    self.current_transition = None

            pygame.display.flip()

        pygame.quit()
        sys.exit()

App().run()