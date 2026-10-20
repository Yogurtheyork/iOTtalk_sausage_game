"""Sausage Toss: a standalone Pygame game, with optional IoTtalk input."""
import argparse
import math
import time
from game_core import World, Throw, GestureController, speed_from_power
from game_input import SensorReceiver, configured_port

WIDTH, HEIGHT = 1100, 760


def project(x, z, y=0):
    scale = 650 / (z + 5)
    return (round(WIDTH/2 + x*scale), round(235 + 2.9*scale - y*scale)), scale


class Game:
    def __init__(self, pygame, receiver, args):
        self.pg, self.receiver, self.args = pygame, receiver, args
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Sausage Toss | 香腸投擲')
        self.world = World()
        self.gesture = GestureController(args.threshold, args.full_strength)
        self.shot = None
        self.charging = None
        self.power = 0.
        self.last_sensor = None
        self.running = True
        self.ready_button = pygame.Rect(830, 620, 220, 58)
        fontpath = None if args.english else pygame.font.match_font('notosanscjktc,notosanscjksc,microsoftjhenghei,pingfangtc,wenquanyizenhei')
        self.zh = bool(fontpath)
        self.font = pygame.font.Font(fontpath, 23)
        self.small = pygame.font.Font(fontpath, 18)
        self.title = pygame.font.Font(fontpath, 44)
        self.background = self.make_background()

    def label(self, en, zh):
        return zh if self.zh else en

    def text(self, value, pos, color=(244, 233, 212), small=False, font=None):
        self.screen.blit((font or (self.small if small else self.font)).render(value, True, color), pos)

    def make_background(self):
        pg = self.pg
        bg = pg.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            if y < 310:
                t = y/310
                c = (int(35+32*t), int(66+35*t), int(76+28*t))
            else:
                t = (y-310)/(HEIGHT-310)
                c = (int(89-46*t), int(91-42*t), int(76-33*t))
            pg.draw.line(bg, c, (0,y), (WIDTH,y))
        pg.draw.circle(bg, (229,188,114), (930,115), 42)
        for x in range(-1200, 2400, 180):
            pg.draw.line(bg, (100,99,78), (550,310), (x,HEIGHT))
        for z in (1,2,3,5,8,13,22):
            y = project(0,z)[0][1]
            pg.draw.line(bg, (100,99,78), (0,y), (WIDTH,y))
        return bg

    def prepare(self, now):
        if self.shot and self.shot.status == 'flying':
            return
        self.shot, self.charging, self.power = None, None, 0.
        # Ignore packets queued before this new attempt.
        self.receiver.poll(now)
        self.gesture.prepare(now)

    def launch(self, power):
        if self.shot is not None:
            return
        self.power = power
        self.shot = Throw(self.world, speed_from_power(power))
        self.gesture.cancel('In flight')
        self.charging = None

    def handle_event(self, event, now):
        pg = self.pg
        if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
            self.running = False
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1 and self.ready_button.collidepoint(event.pos):
            self.prepare(now)
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_r:
                self.prepare(now)
            elif event.key == pg.K_SPACE and self.shot is None and self.charging is None:
                self.charging = now
                self.gesture.cancel('Keyboard charging')
        elif event.type == pg.KEYUP and event.key == pg.K_SPACE and self.charging is not None:
            self.launch(min(1., max(0., (now-self.charging)/1.5)))
        elif event.type == pg.WINDOWFOCUSLOST:
            self.charging = None

    def update(self, now, dt):
        for stamp, axes in self.receiver.poll(now):
            self.last_sensor = stamp
            if self.charging is None and self.shot is None:
                self.gesture.feed(axes, stamp)
        power = self.gesture.update(now)
        if power is not None and self.shot is None and self.charging is None:
            self.launch(power)
        if self.charging is not None:
            self.power = min(1., (now-self.charging)/1.5)
        if self.shot:
            self.shot.advance(dt)

    def table(self):
        pg, w = self.pg, self.world
        near_left = project(-w.half_width,w.near,w.table_height)[0]
        near_right = project(w.half_width,w.near,w.table_height)[0]
        far_left = project(-w.half_width,w.far,w.table_height)[0]
        far_right = project(w.half_width,w.far,w.table_height)[0]
        for x in (-w.half_width+.15, w.half_width-.15):
            for z in (w.far-.15, w.near+.15):
                pg.draw.line(self.screen,(58,36,29),project(x,z)[0],project(x,z,w.table_height)[0],12)
        pg.draw.polygon(self.screen,(92,49,33),[near_left,near_right,(near_right[0],near_right[1]+15),(near_left[0],near_left[1]+15)])
        pg.draw.polygon(self.screen,(182,124,66),[near_left,near_right,far_right,far_left])
        pg.draw.lines(self.screen,(235,177,96),True,[near_left,near_right,far_right,far_left],3)
        for z in (5.5,6,6.5,7):
            pg.draw.line(self.screen,(160,102,54),project(-w.half_width,z,w.table_height)[0],project(w.half_width,z,w.table_height)[0],2)
        # The inset marks where the entire sausage fits, not a screen-space hitbox.
        inset = [project(x,z,w.table_height+.002)[0] for x,z in [(-1.,5.3),(1.,5.3),(1.,7.2),(-1.,7.2)]]
        pg.draw.lines(self.screen,(244,211,130),True,inset,2)
        self.text(self.label('LAND ON THE TABLE', '把香腸丟到桌上'), (435,160), small=True)

    def pot(self):
        pg = self.pg
        pg.draw.ellipse(self.screen,(32,39,39),(390,559,320,64))
        pg.draw.polygon(self.screen,(53,68,72),[(382,470),(718,470),(682,586),(418,586)])
        pg.draw.ellipse(self.screen,(91,111,115),(380,426,340,100))
        pg.draw.ellipse(self.screen,(30,43,46),(394,437,312,75))
        pg.draw.ellipse(self.screen,(119,134,129),(380,426,340,100),5)
        pg.draw.ellipse(self.screen,(121,133,128),(332,456,65,32),8)
        pg.draw.ellipse(self.screen,(121,133,128),(703,456,65,32),8)
        pg.draw.arc(self.screen,(166,178,162),(415,390,45,50),0,2.4,2)
        pg.draw.arc(self.screen,(166,178,162),(625,385,35,50),0,2.4,2)

    def sausage(self):
        pg = self.pg
        if self.shot is None:
            center, scale = project(0, 0, self.world.start_height+self.world.radius)
        else:
            s = self.shot
            center, scale = project(s.x,s.z,s.y+self.world.radius)
            shadow_y = self.world.table_height if s.status == 'success' else 0
            if self.world.near <= s.z <= self.world.far and s.y >= self.world.table_height:
                shadow_y = self.world.table_height
            shadow, _ = project(s.x,s.z,shadow_y)
            pg.draw.ellipse(self.screen,(53,48,36),(shadow[0]-scale*.62,shadow[1]-scale*.07,scale*1.24,scale*.14))
        half = max(4, round(scale*(self.world.sausage_half-self.world.radius)))
        radius = max(3, round(scale*self.world.radius))
        x,y = center
        pg.draw.line(self.screen,(91,36,28),(x-half,y+2),(x+half,y+2),radius*2+5)
        pg.draw.line(self.screen,(198,73,41),(x-half,y),(x+half,y),radius*2)
        pg.draw.circle(self.screen,(198,73,41),(x-half,y),radius)
        pg.draw.circle(self.screen,(198,73,41),(x+half,y),radius)
        pg.draw.line(self.screen,(246,145,79),(x-half+radius,y-radius//2),(x+half-radius,y-radius//2),max(2,radius//3))
        for offset in (-.32,0,.32):
            a = round(x+offset*scale)
            pg.draw.line(self.screen,(133,46,29),(a-3,y-3),(a+3,y+4),max(2,radius//5))

    def draw(self, now):
        pg = self.pg
        self.screen.blit(self.background,(0,0))
        self.text('SAUSAGE TOSS', (42,32), font=self.title)
        self.text(self.label('A little swing. A perfect landing.', '揮一下，把香腸送上桌。'),(44,88),small=True)
        self.table()
        self.pot()
        if self.shot and self.shot.z > self.world.far and self.shot.y < self.world.table_height:
            self.sausage(); self.table()
        else:
            self.sausage()
        connected = self.last_sensor is not None and now-self.last_sensor <= 1
        dot = (115,214,162) if connected else (176,167,144)
        pg.draw.circle(self.screen,dot,(847,41),5)
        self.text(self.label('PHONE ONLINE' if connected else 'KEYBOARD / NO PHONE', '手機已連線' if connected else '鍵盤模式／等待手機'),(863,31),small=True)
        pg.draw.rect(self.screen,(29,42,44),(28,614,1044,122),border_radius=16)
        if self.shot:
            messages = {'flying':('Into the distance...', '香腸飛行中…'), 'success':('PERFECT LANDING!', '成功！香腸上桌了！'), 'short':('Too short - swing harder', '力道不足，再用力一點'), 'long':('Too far - use less power', '飛過頭了，輕一點'), 'edge':('Clipped the edge - try again', '碰到桌邊，再試一次')}
            en,zh = messages[self.shot.status]
            message = self.label(en,zh)
        elif self.charging is not None:
            message = self.label('Release SPACE to throw', '放開空白鍵投擲')
        else:
            translations = {'Press READY':'按準備，或直接按住空白鍵', 'Hold phone still for 1 second':'保持手機靜止一秒', 'Swing forward!':'往前揮手機！', 'Phone disconnected - prepare again':'手機資料中斷，請重新準備', 'Calibration failed - keep phone still':'校正失敗，請保持手機靜止', 'Not enough samples - prepare again':'樣本不足，請重新準備', 'Too few phone samples - check sensor rate':'手機資料太少，請檢查傳送頻率', 'Phone still moving - rest it on a table and retry':'手機仍在晃動，請放桌上再準備', 'Ready timed out':'等待逾時，請重新準備'}
            message = self.label(self.gesture.message, translations.get(self.gesture.message,self.gesture.message))
            if self.gesture.state == 'calibrating':
                n = len(self.gesture.samples)
                values = [v for _, v in self.gesture.samples]
                spread = max(values)-min(values) if values else 0.
                message = self.label(f'Hold still... samples {n}/5+, variation {spread:.1f}/2.0', f'保持靜止… 樣本 {n}/5+，變動 {spread:.1f}/2.0')
        self.text(message,(50,633),(247,206,121))
        self.text(self.label('Hold SPACE: power  /  R: ready & retry  /  ESC: quit', '按住空白鍵蓄力 ／ R 準備、重玩 ／ Esc 離開'),(50,674),small=True)
        pg.draw.rect(self.screen,(66,79,76),(50,706,700,9),border_radius=4)
        if self.power > 0:
            pg.draw.rect(self.screen,(232,161,82),(50,706,round(700*self.power),9),border_radius=4)
        pg.draw.rect(self.screen,(225,163,83),self.ready_button,border_radius=12)
        self.text(self.label('READY / RETRY', '準備／再玩一次'),(850,638),(38,43,38))
        self.text(f'{self.power*100:.0f}%   |   sensor {self.gesture.strength:.1f}',(832,697),small=True)
        pg.display.flip()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=configured_port())
    parser.add_argument('--threshold',type=float,default=2.)
    parser.add_argument('--full-strength',type=float,default=20.)
    parser.add_argument('--english',action='store_true')
    parser.add_argument('--frames',type=int,default=0,help='Exit after N frames (0 = unlimited)')
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535 or args.frames < 0:
        parser.error('Invalid port or frames')
    if not math.isfinite(args.threshold) or not math.isfinite(args.full_strength) or not 0 < args.threshold < args.full_strength:
        parser.error('Require finite 0 < threshold < full-strength')
    try:
        import pygame
    except ImportError:
        print('Install Pygame: python -m pip install -r requirements-game.txt')
        return 1
    try:
        receiver = SensorReceiver(args.port)
    except OSError as error:
        print(f'Cannot open local sensor port {args.port}: {error}. Try --port 8766 (and SAUSAGE_PORT=8766 for SA_game).')
        return 1
    try:
        pygame.init()
        game = Game(pygame,receiver,args)
        clock = pygame.time.Clock()
        frames = 0
        while game.running:
            dt = clock.tick(60)/1000
            now = time.monotonic()
            for event in pygame.event.get(): game.handle_event(event,now)
            game.update(now,dt)
            game.draw(now)
            frames += 1
            if args.frames and frames >= args.frames: break
        return 0
    finally:
        receiver.close()
        pygame.quit()


if __name__ == '__main__':
    raise SystemExit(main())
