"""Deterministic world physics and one-shot gesture detection (no UI dependencies)."""
from dataclasses import dataclass
import math
import statistics


@dataclass(frozen=True)
class World:
    gravity: float = 9.8
    start_height: float = 1.1
    table_height: float = 1.5
    near: float = 5.0
    far: float = 7.5
    half_width: float = 1.8
    sausage_half: float = .65
    radius: float = .12


def speed_from_power(power: float) -> float:
    if not math.isfinite(power):
        raise ValueError('Power must be finite')
    return 4 + 8 * max(0, min(1, power))


class Throw:
    def __init__(self, world: World, speed: float):
        if not math.isfinite(speed) or not 0 <= speed <= 100:
            raise ValueError('Invalid speed')
        self.world = world
        self.vz = self.vy = speed / math.sqrt(2)
        self.x, self.y, self.z = 0., world.start_height, 0.
        self.time = 0.
        self.status = 'flying'
        self.checked_table = False
        self.edge = False
        self.miss = 'short'

    def position(self, t):
        return self.world.start_height + self.vy*t - .5*self.world.gravity*t*t, self.vz*t

    def advance(self, dt: float) -> None:
        if not math.isfinite(dt) or dt < 0:
            raise ValueError('dt must be nonnegative and finite')
        if self.status != 'flying':
            return
        self.time += dt
        w = self.world
        discriminant = self.vy**2 + 2*w.gravity*(w.start_height-w.table_height)
        if not self.checked_table and discriminant >= 0:
            contact = (self.vy + math.sqrt(discriminant))/w.gravity
            if self.time >= contact:
                self.checked_table = True
                z = self.vz*contact
                inside = (abs(self.x)+w.sausage_half <= w.half_width
                          and w.near+w.radius <= z <= w.far-w.radius)
                overlap = (abs(self.x)-w.sausage_half < w.half_width
                           and w.near-w.radius < z < w.far+w.radius)
                if inside:
                    self.y, self.z, self.status = w.table_height, z, 'success'
                    return
                self.edge = overlap
                self.miss = 'short' if z < w.near else 'long'
        ground_time = (self.vy + math.sqrt(self.vy**2 + 2*w.gravity*w.start_height))/w.gravity
        if self.time >= ground_time:
            self.y, self.z = 0., self.vz*ground_time
            self.status = 'edge' if self.edge else self.miss
        else:
            self.y, self.z = self.position(self.time)


class GestureController:
    def __init__(self, threshold=2., full_strength=20.):
        if not 0 < threshold < full_strength or not math.isfinite(full_strength):
            raise ValueError('Require 0 < threshold < full_strength')
        self.threshold, self.full_strength = threshold, full_strength
        self.reset()

    def reset(self):
        self.state, self.message = 'idle', 'Press READY'
        self.baseline = self.strength = self.peak = 0.
        self.samples = []
        self.last = None

    def prepare(self, now):
        self.reset()
        self.started = now
        self.state, self.message = 'calibrating', 'Hold phone still for 1 second'

    def feed(self, axes, now):
        if self.state not in ('calibrating', 'ready', 'capturing') or now < self.started:
            return
        if self.last is not None and now - self.last > 1:
            self.cancel('Phone disconnected - prepare again')
            return
        self.last = now
        magnitude = math.hypot(*axes)
        if self.state == 'calibrating':
            self.samples.append((now, magnitude))
            # A rolling window lets motion from pressing READY settle naturally.
            self.samples = [(t, value) for t, value in self.samples if now-t <= 2.01][-256:]
            values = [value for _, value in self.samples]
            enough = len(values) >= 5 and now-self.samples[0][0] >= 1
            if enough and max(values)-min(values) <= 2:
                self.baseline = statistics.median(values)
                self.state, self.message, self.ready_at = 'ready', 'Swing forward!', now
            elif now-self.started >= 5:
                self.calibration_timeout()
            return
        self.strength = max(0., magnitude-self.baseline)
        if self.state == 'ready' and now-self.ready_at >= 10:
            self.cancel('Ready timed out')
            return
        if self.state == 'ready' and self.strength > self.threshold:
            self.state, self.capture_at = 'capturing', now
        if self.state == 'capturing' and now-self.capture_at <= .25:
            self.peak = max(self.peak, self.strength)

    def calibration_timeout(self):
        if len(self.samples) < 5:
            self.cancel('Too few phone samples - check sensor rate')
        else:
            self.cancel('Phone still moving - rest it on a table and retry')

    def cancel(self, message):
        self.state, self.message = 'idle', message

    def update(self, now):
        if self.state in ('calibrating', 'ready', 'capturing'):
            if (self.last is None and now-self.started > 1) or (self.last is not None and now-self.last > 1):
                self.cancel('Phone disconnected - prepare again')
            elif self.state == 'calibrating' and now-self.started >= 5:
                self.calibration_timeout()
            elif self.state == 'ready' and now-self.ready_at >= 10:
                self.cancel('Ready timed out')
            elif self.state == 'capturing' and now-self.capture_at >= .25:
                self.state, self.message = 'consumed', 'Throw!'
                return min(1., self.peak/self.full_strength)
        return None
