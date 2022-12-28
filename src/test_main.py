from main import hello_world, one
import unittest


class TestMain(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(hello_world(),
                         "Hello world!")

    def test_one(self):
        self.assertEqual(one(),  1)


if __name__ == '__main__':
    unittest.main()
