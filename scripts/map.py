import pygame
import json
from scripts import utils
from scripts import consts
import random

class Map:
    def __init__(self, tile_size=None):
        self.tile_size = tile_size
        self.load_map('maps/map.json')
        self.k = self.tile_size / self.base_tile_size
        self.resources, self.resource_props = utils.load_resources('data/resources', self.k, (255, 255, 255))
        # screen shaking
        self.screen_start_shaking = 0
        self.screen_shaking = 0
        self.shake_intensity = 1
        self.screen_offset = [0, 0]

        # background
        self.background_tile = utils.load_image('data/resources/tiles/tile16.png', self.k)

    def shake_screen(self, delay=30, intensity=1):
        self.screen_start_shaking = self.screen_shaking = delay
        self.shake_intensity = intensity

    def get_offgrid_tiles(self, resource_name, variant, keep=False):
        '''
        @ return [(pos, tile),]
        '''
        results = []
        for tile in self.offgrid_tiles:
            pos = tile['pos']
            if tile['resource'] == resource_name and tile['variant'] == variant:
                results.append((pos, tile))
        if not keep:
            for _, tile in results:
                self.offgrid_tiles.remove(tile)
        return results

    def get_tiles(self, resource_name, variant, absolute=True,keep=False):
        '''
        @ absolute - if True then returns absolute coords. Otherwise it returns relative (grid coords)
        @ return [(pos, tile),]
        '''
        results = []
        for pos, tile in self.tile_map.items():
            if tile['resource'] == resource_name and tile['variant'] == variant:
                if absolute:
                    pos = (pos[0] * self.tile_size, pos[1] * self.tile_size)
                results.append((pos, tile))
        if not keep:
            for pos, tile in results:
                if absolute:
                    pos = (pos[0] // self.tile_size, pos[1] // self.tile_size)
                del self.tile_map[pos]
        return results


    def issolid(self, x, y):
        tx = x // self.tile_size
        ty = y // self.tile_size
        if (tx, ty) not in self.tile_map: return False
        tile = self.tile_map[(tx, ty)]
        resource_name = tile['resource']
        variant = tile['variant']
        if 'solid' not in self.resource_props[resource_name]: return False
        return self.resource_props[resource_name]['solid'][variant]
        
    def get_solid_intersections(self, rect):
        intersections = []
        i_start = rect.left // self.tile_size
        i_end = rect.right // self.tile_size
        j_start = rect.top // self.tile_size
        j_end = rect.bottom // self.tile_size
        for i in range(i_start, i_end + 1):
            for j in range(j_start, j_end + 1):
                if self.issolid(i * self.tile_size, j * self.tile_size):
                    x_ = i * self.tile_size
                    y_ = j * self.tile_size
                    tile_rect = pygame.Rect(x_, y_, self.tile_size, self.tile_size)
                    if tile_rect.colliderect(rect):
                        intersections.append(tile_rect)
        return intersections


    def load_map(self, path):
        with open(path, 'r') as f:
            data = json.load(f)
            self.tile_map = {
                tuple(map(int, k[1:-1].split(','))): v
                for k, v in data['tile_map'].items()
            }
            self.offgrid_tiles = data['nogrid_tiles']
            self.base_tile_size = data['base_tile_size']
            self.tile_size = data['tile_size']
            self.k = self.tile_size / self.base_tile_size
            self.camera_x = data['camera_x'] #// self.k_last * self.k  # * self.tile_size
            self.camera_y = data['camera_y'] #// self.k_last * self.k # * self.tile_size

    def _render_background(self, surf):
        surf.fill((20,) * 3)

    def render(self, surf):   
        self._render_background(surf) 
        i_start = int(self.camera_x // self.tile_size) - 1
        i_end = int((self.camera_x + surf.get_width()) // self.tile_size) + 1
        j_start = int(self.camera_y // self.tile_size) - 1
        j_end = int((self.camera_y + surf.get_height()) // self.tile_size) + 1
        for i in range(i_start, i_end + 1):
            for j in range(j_start, j_end + 1):
                if (i, j) in self.tile_map:
                    tile = self.tile_map[(i, j)]
                    img = self.resources[tile['resource']][tile['variant']]
                    surf.blit(img, (i * self.tile_size - self.camera_x, j * self.tile_size - self.camera_y))
        for tile in self.offgrid_tiles:
            x = tile['pos'][0] * self.k - self.camera_x
            y = tile['pos'][1] * self.k - self.camera_y
            if 0 <= x <= surf.get_width() and 0 <= y <= surf.get_height():
                img = self.resources[tile['resource']][tile['variant']]
                surf.blit(img, (x, y))

    def update(self):
        self.screen_shaking = max(0, self.screen_shaking - 1)
        if self.screen_shaking > 0:
            self.screen_offset = [
                random.randint(-self.shake_intensity, self.shake_intensity) / (self.screen_start_shaking + 1 - self.screen_shaking)
                for _ in range(2)
            ]
            self.camera_x += self.screen_offset[0]
            self.camera_y += self.screen_offset[1]
        