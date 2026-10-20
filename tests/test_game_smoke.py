import os
import subprocess
import sys
import unittest

class SmokeTests(unittest.TestCase):
    def test_headless_start_exit(self):
        env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
        result = subprocess.run([sys.executable, 'game.py', '--english', '--frames', '5', '--port', '0'], env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_keyboard_and_sensor_play(self):
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        import pygame
        from argparse import Namespace
        from game import Game
        from game_input import SensorReceiver, send_axes
        pygame.init()
        receiver = SensorReceiver(0)
        try:
            game = Game(pygame, receiver, Namespace(english=True, threshold=2., full_strength=20.))
            game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE), 0)
            game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_SPACE), .75)
            game.update(.75, 10)
            self.assertEqual(game.shot.status, 'success')
            game.draw(.75)
            pygame.image.save(game.screen, '/tmp/sausage-success.png')
            game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_r), 2)
            self.assertIsNone(game.shot)
            port = receiver.socket.getsockname()[1]
            for i in range(11):
                send_axes((0,0,10), port)
                game.update(2+i/10, 0)
            self.assertEqual(game.gesture.state, 'ready')
            send_axes((0,0,20), port); game.update(3.1, 0)
            game.update(3.36, 0)
            self.assertIsNotNone(game.shot)
            game.update(3.5, 10)
            self.assertEqual(game.shot.status, 'success')
            game.prepare(4)
            game.draw(4)
            pygame.image.save(game.screen, '/tmp/sausage-ready.png')
            game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE), 5)
            self.assertFalse(game.running)
        finally:
            receiver.close()
            pygame.quit()
