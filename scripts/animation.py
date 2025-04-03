import pygame
from scripts import utils
import os 

class BaseAnimation:
    def __init__(self, frames, frame_duration, repeat=True):
        self.frames = frames
        self.flipped_frames = None
        self.frame_duration = frame_duration
        self.repeat = repeat

        self.current_frame = 0
        self.frame_timer = 0
        self.finished = False

    def make_flipped(self, colorkey=None):
        self.flipped_frames = []
        for frame in self.frames:
            frame = pygame.transform.flip(frame, True, False)
            if colorkey:
                frame.set_colorkey(colorkey)
            self.flipped_frames.append(frame)
        

    def update(self):
        self.finished = False
        self.frame_timer += 1
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1)
            if self.current_frame == len(self.frames):
                self.current_frame = 0 if self.repeat else self.current_frame - 1
                self.finished = True
        
    def get_current_frame(self):
        return self.frames[self.current_frame]
    
    def reset(self):
        self.current_frame = 0
        self.frame_timer = 0

    def render(self, surf, pos, flip=False):
        image = self.frames[self.current_frame]
        if flip:
            image = self.flipped_frames[self.current_frame]
        surf.blit(image, pos)


class Animation(BaseAnimation):
    def __init__(self, base_dir, anim_name, num_of_frames, frame_duration, scale=1, colorkey=None, repeat=True):
        super().__init__(None, frame_duration, repeat)
        self.anim_name = anim_name
        self.path = os.path.join(base_dir, anim_name)
        self.num_of_frames = num_of_frames
        self.frames = utils.crop_images(
            utils.load_image(self.path, scale),
            num_of_frames,
            colorkey=colorkey
        )
        self._max_width = max([x.get_width() for x in self.frames])
        self._max_height = max([x.get_height() for x in self.frames])
        if colorkey:
            for x in self.frames: x.set_colorkey(colorkey)
        self.make_flipped(colorkey=colorkey)

        
class ListOfFilesAnimation(BaseAnimation):
    def __init__(self, dirpath, frame_duration, scale=1, repeat=False, colorkey=None, size=None, bounding=False):
        super().__init__(None, frame_duration, repeat)
        self.frames = utils.load_images(dirpath, scale, colorkey, size=size, bounding=bounding)
        self.make_flipped(colorkey=colorkey)
        self._max_width = max([x.get_width() for x in self.frames])
        self._max_height = max([x.get_height() for x in self.frames])
        
    
class JoinFilesAnimation(BaseAnimation):
    def __init__(self, dirpath, pattern, frame_duration, scale=1, colorkey=None, size=None, repeat=True):
        super().__init__(None, frame_duration, repeat)
        self.frames = utils.join_images(dirpath, pattern, scale, size, colorkey)
        self.make_flipped(colorkey=colorkey)
        self._max_width = max([x.get_width() for x in self.frames])
        self._max_height = max([x.get_height() for x in self.frames])


