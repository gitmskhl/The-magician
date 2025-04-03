import pygame
import os

def resize_frames(animations: dict, colorkey: tuple[int]=None, exceptions=['attack_1', 'attack_2', 'attack_3']):
    width = animations[max(animations, key=lambda x: animations[x]._max_width if x not in exceptions else 0)]._max_width
    height = animations[max(animations, key=lambda x: animations[x]._max_height if x not in exceptions else 0)]._max_height

    for anim_name, animation in animations.items():
        if anim_name in exceptions: continue
        animation.frames  = [
            pygame.transform.scale(frame, (width, height))
            for frame in animation.frames 
        ]
        if colorkey:
            for frame in animation.frames:
                frame.set_colorkey(colorkey)

def load_image(path, scale, colorkey=None, size=None, bounding=False):
    image = pygame.image.load(path).convert_alpha()
    if size is not None:
        image = pygame.transform.scale(image, size)
    else:
        image = pygame.transform.scale(image, (int(image.get_width() * scale), int(image.get_height() * scale)))
    # if colorkey:
    #     image.set_colorkey(colorkey)
    if bounding:
        brect = image.get_bounding_rect()
        surf = pygame.Surface(brect.size)
        surf.blit(image, (0, 0), brect)
        image = surf
    if size is not None:
        image = pygame.transform.scale(image, size)
    if colorkey:
        image.set_colorkey(colorkey)
    return image


def crop_images(sheet, num_sprites, colorkey=None, bounding=True):
    images = []
    sheet_size = sheet.get_size()
    sprite_width = sheet_size[0] // num_sprites
    sprite_height = sheet_size[1]
    for i in range(num_sprites):
        surf = pygame.Surface((sprite_width, sprite_height))
        surf.blit(sheet, (0, 0), (i * sprite_width, 0, sprite_width, sprite_height))
        img = surf
        if colorkey:
            img.set_colorkey(colorkey)
        if bounding:
            brect = img.get_bounding_rect()
            surf_ = pygame.Surface(brect.size)
            surf_.blit(img, (0, 0), brect)
            img = surf_
        images.append(img)
    return images

def load_images(directory, scale, colorkey=None, size=None, bounding=True):
    images = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith('.png') or filename.endswith('.jpg'):
            path = os.path.join(directory, filename)
            image = load_image(path, scale, colorkey, size=size, bounding=bounding)
            images.append(image)
    return images


def resize_resources(resourcesdir_path, scale, colorkey=None):
        resources = {}
        for dirname in os.listdir(os.path.join(resourcesdir_path)):
            path = os.path.join(resourcesdir_path, dirname)
            resources[dirname] = load_images(path, scale, colorkey)
        return resources


def load_resources(resourcesdir_path, scale, colorkey=None):
    '''
    resourcesdir_path: str - path to the resources directory
    return resources, resource_props
    '''
    resource_props = {}
    for dirname in os.listdir(resourcesdir_path):
        path = os.path.join(resourcesdir_path, dirname)
        res_count = len(os.listdir(path))
        info_path = os.path.join(path, 'info.txt')
        resource_props[dirname] = {}
        if os.path.exists(info_path):
            with open(info_path, 'r') as f:
                for line in f:
                    lst = line.split(':')
                    prop = lst[0].strip()
                    if len(lst) == 1:
                        resource_props[dirname][prop] = [True] * res_count
                    else:
                        resource_props[dirname][prop] = [False] * res_count
                        idxs = [int(i) for i in lst[1].split(' ') if i]
                        for i in idxs:
                            resource_props[dirname][prop][int(i)] = True
    resources = resize_resources(resourcesdir_path, scale, colorkey)
    return resources, resource_props


def join_images(dirpath, pattern, scale, size=None, colorkey=None):
    '''
    dirpath - directory path
    patter - pattern in names of the files to be joined 
    '''
    images = [load_image(os.path.join(dirpath, filename), 1, colorkey=False, bounding=True) for filename in sorted(os.listdir(dirpath)) if filename.startswith(pattern)]
    result = []
    for image in images:
        w = image.get_width() * scale
        h = image.get_height() * scale
        if size:
            w, h = size
        img = pygame.transform.scale(image, (w, h))
        if colorkey:
            img.set_colorkey(colorkey)
        result.append(img)
    return result
