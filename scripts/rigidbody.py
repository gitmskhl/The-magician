import pygame
from .map import Map

class StaticRigidBody:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
    
    def collidex(self, otherrect: pygame.Rect, velx: float) -> bool:
        if not self.rect.colliderect(otherrect): return False
        if velx > 0:
            otherrect.right = self.rect.left
        elif velx< 0:
            otherrect.left = self.rect.right
        return True
    
    def collidey(self, otherrect: pygame.Rect, vely: float) -> bool:
        if not self.rect.colliderect(otherrect): return False
        if vely > 0:
            otherrect.bottom = self.rect.top
        elif vely< 0:
            otherrect.top = self.rect.bottom
        return True

    def collide(self, otherrect: pygame.Rect, vel: list[float, float]):
        '''
        Not recommended to use! Instead of it use collidex & collidey
        '''
        if not self.rect.colliderect(otherrect): return False
        return self.collidex(otherrect, vel[0]) or self.collidey(otherrect, vel[1])
    

class DynamicRigidBody:
    def __init__(self, rect: pygame.Rect, vel: list[float, float], map: Map):
        self.rect = rect
        self.vel = list(vel)
        self.map = map
        self.collision = {'left': False, 'right': False, 'up': False, 'down': False}

    def _correctPositionx(self, rigidBodies: list[pygame.Rect]):
        for rect in rigidBodies:
            if rect.colliderect(self.rect):
                if self.vel[0] > 0:
                    self.rect.right = rect.left
                    self.collision['right'] = True
                elif self.vel[0] < 0:
                    self.rect.left = rect.right
                    self.collision['left'] = True

    def movex(self, rigidBodies: list[pygame.Rect]):
        self.collision['left'] = self.collision['right'] = False
        self.rect.x += self.vel[0]
        self._correctPositionx(self.map.get_solid_intersections(self.rect))
        self._correctPositionx(rigidBodies)
        

    def _correctPositiony(self, rigidBodies: list[pygame.Rect]):
        for rect in rigidBodies:
            if rect.colliderect(self.rect):
                if self.vel[1] > 0:
                    self.rect.bottom = rect.top
                    self.collision['down'] = True
                elif self.vel[1] < 0:
                    self.rect.top = rect.bottom
                    self.collision['up'] = True

    def movey(self, rigidBodies: list[pygame.Rect]):
        self.collision['up'] = self.collision['down'] = False
        self.rect.y += self.vel[1]
        self._correctPositiony(self.map.get_solid_intersections(self.rect))
        self._correctPositiony(rigidBodies)

    def update(self, rigidBodies: list[pygame.Rect]=[]):
        self.movex(rigidBodies)
        self.movey(rigidBodies)

