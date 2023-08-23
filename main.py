import pygame
import time
import random

WIN_WIDTH = 500
WIN_HEIGHT = 800

bird_imgs = [pygame.transform.scale2x(pygame.image.load(f"flappy_bird/assets/bird{x}.png")) for x in range(1,4)]
pipe_img = pygame.transform.scale2x(pygame.image.load(f"flappy_bird/assets/pipe.png"))
bg_img = pygame.transform.scale2x(pygame.image.load(f"flappy_bird/assets/bg.png"))
base_img = pygame.transform.scale2x(pygame.image.load(f"flappy_bird/assets/base.png"))


class Bird:
    IMGS = bird_imgs
    ACCEL_Y = 3
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self,x ,y) -> None:
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1

        # Handle movement
        s = (self.vel*self.tick_count) + (0.5*self.ACCEL_Y*self.tick_count**2) # s = vt+.5at^2

        if s >=16: # Max Fall Distance in 1 frame (pixels/second) Velocity
            s = 16
        
        if s < 0: # Max Rise Distance in 1 frame (pixels/second) Velocity
            s -= 2
        
        self.y = self.y + s

        # Handle tilting
        if s < 0 or self.y < self.height + 50: # if s < 0 (is the bird moving up)
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1
        
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0
        
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        rotated_img = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_img.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
        
        win.blit(rotated_img, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x) -> None:
        self.x = x
        self.height = 0
        
        self.top = 0
        self.bottom = 0

        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img

        self.passed = False

        self.set_height()

    def set_height(self):
        self.height = random.randrange(50 , 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird: Bird):
        bird_mask = bird.get_mask()
        top_pipe_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_pipe_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_pipe_mask, bottom_offset)
        t_point = bird_mask.overlap(top_pipe_mask, top_offset)
        
        if b_point or t_point:
            return True
        
        return False

def draw_window(win, bird, pipes):
    win.blit(bg_img, (0,0))
    bird.draw(win)
    for pipe in pipes:
        pipe.draw(win)
    pygame.display.update()



def main():
    bird = Bird(200,200)
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    run = True

    clock = pygame.time.Clock()

    pipes = [Pipe(700)]

    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                run = False
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                bird.jump()

        bird.move()

        rem = []
        for pipe in pipes:
            pipe.move()

            if pipe.collide(bird):
                print("Hit!")


            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                pipes.append(Pipe(WIN_WIDTH))

            if pipe.x + pipe.PIPE_TOP.get_width() < 0: # Check if the pipe is to left of the window (outside of view)
                rem.append(pipe)
        
        for r in rem:
            pipes.remove(r)

        draw_window(win, bird, pipes)
    
    pygame.quit()




if __name__ == "__main__":
    main()