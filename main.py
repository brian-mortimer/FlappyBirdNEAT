import pygame
import time
import random
import os
import neat as neat

pygame.font.init()

WIN_WIDTH = 500
WIN_HEIGHT = 800
STAT_FONT = pygame.font.SysFont("comicsans", 50)

BIRD_X = 230
FLOOR = 730

bird_imgs = [pygame.transform.scale2x(pygame.image.load(f"flappy_bird/assets/bird{x}.png")) for x in range(1,4)]
pipe_img = pygame.transform.scale2x(pygame.image.load(f"flappy_bird/assets/pipe.png"))
bg_img = pygame.transform.scale2x(pygame.image.load(f"flappy_bird/assets/bg.png"))
base_img = pygame.transform.scale2x(pygame.image.load(f"flappy_bird/assets/base.png"))

MOVE_VEL = 5
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

gen = 0

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
        self.x -= MOVE_VEL

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
    
class Base:
    WIN_WIDTH = WIN_WIDTH
    WIDTH = base_img.get_width()
    IMG = base_img

    def __init__(self, y) -> None:
        self.x1 = 0
        self.x2 = self.WIDTH
        self.y = y

    def move(self):
        self.x1 -= MOVE_VEL
        self.x2 -= MOVE_VEL

        if self.x1 + self.WIDTH < 0: # is right edge of the image outside of window
            self.x1 = self.x2 + self.WIDTH
        
        if self.x2 + self.WIDTH < 0: # is right edge of the image outside of window
            self.x2 = self.x1 + self.WIDTH

    
    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score, gen):
    if gen == 0:
        gen = 1

    win.blit(bg_img, (0,0))
    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    for bird in birds:
        bird.draw(win)

    score_label = STAT_FONT.render(f"Score: {score}", 1, (255,255,255))
    win.blit(score_label, ((WIN_WIDTH/2)-(score_label.get_width()/2), 20))

    pygame.display.update()



def eval_genomes(genomes, config):
    global gen, WIN
    win = WIN
    nets = []
    ge = []
    birds = []

    gen += 1

    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(BIRD_X,350))
        ge.append(genome)

    pipes = [Pipe(700)]
    base = Base(FLOOR)
    clock = pygame.time.Clock()

    run = True
    score = 0
    while run and len(birds) > 0:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        # Handle Bird movement and jumping
        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():  # determine whether to use the first or second
                pipe_ind = 1                                                                 # pipe on the screen for neural network input

        for x, bird in enumerate(birds):  # give each bird a fitness of 0.1 for each frame it stays alive
            ge[x].fitness += 0.1
            bird.move()

            # send bird location, top pipe location and bottom pipe location and determine from network whether to jump or not
            output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:  # we use a tanh activation function so result will be between -1 and 1. if over 0.5 jump
                bird.jump()

        base.move()
        rem = []
        add_pipe = False

        for pipe in pipes:
            pipe.move()

            for i, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))


            # Check if passed the pipe
            if not pipe.passed and pipe.x < BIRD_X:
                pipe.passed = True
                add_pipe = True

            # if the pipe is to left of the window (outside of view) add it to remove list
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

        # Add new pipes
        if add_pipe:
            score += 1
            # for genome in ge:
            #     genome.fitness += 5
            pipes.append(Pipe(WIN_WIDTH))
        
        # Remove Pipes passed
        for r in rem:
                pipes.remove(r)

        for bird in birds:
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50:
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))

        draw_window(win, birds, pipes, base, score, gen)

def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                            neat.DefaultSpeciesSet, neat.DefaultStagnation,
                            config_path)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    #p.add_reporter(neat.Checkpointer(5))

    # Run for up to 50 generations.
    winner = p.run(eval_genomes, 50)

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    config_path = "C:/Users/Brian/Desktop/Projects/Python/SnakeAI/config-feedforward.txt"
    run(config_path)