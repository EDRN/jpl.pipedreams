# encoding: utf-8

from .template import Template


class Testing(Template):
    def __init__(self):
        super().__init__()

    def test(self, x):
        return x + 1

    def test_wait(self, x):
        y = 0
        for i in range(10000000):
            y += 1
        return x
