import socket
import unittest
from game_input import parse_axes, send_axes, SensorReceiver

class InputTests(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(parse_axes([1,2,3]), (1.,2.,3.))
        self.assertEqual(parse_axes([[1,2,3]]), (1.,2.,3.))
        for value in [None, [True,2,3], [float('nan'),2,3], [float('inf'),2,3], [1e308,0,0], [1,2], [[[1,2,3]]], ['1',2,3]]:
            self.assertIsNone(parse_axes(value))
    def test_loopback(self):
        receiver = SensorReceiver(0)
        try:
            port = receiver.socket.getsockname()[1]
            send_axes((1,2,3), port)
            self.assertEqual(receiver.poll(10), [(10, (1.,2.,3.))])
            sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            with sender:
                sender.sendto(b'garbage', ('127.0.0.1', port))
                sender.sendto(b'x'*300, ('127.0.0.1', port))
            self.assertEqual(receiver.poll(11), [])
            with self.assertRaises(OSError): SensorReceiver(port)
        finally: receiver.close()
        send_axes((0,0,0), port)
    def test_overload_clears_backlog(self):
        receiver = SensorReceiver(0)
        try:
            port = receiver.socket.getsockname()[1]
            for i in range(100): send_axes((i,0,0), port)
            self.assertEqual(receiver.poll(5), [])
            self.assertEqual(receiver.poll(6), [])
            send_axes((1,2,3), port)
            self.assertEqual(receiver.poll(7), [(7,(1.,2.,3.))])
        finally: receiver.close()

    def test_burst_latest(self):
        receiver = SensorReceiver(0)
        try:
            port = receiver.socket.getsockname()[1]
            for i in range(10): send_axes((i,0,0), port)
            self.assertEqual(receiver.poll(5), [(5,(9.,0.,0.))])
        finally: receiver.close()
