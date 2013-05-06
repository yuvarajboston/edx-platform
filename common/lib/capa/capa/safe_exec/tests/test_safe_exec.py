"""Test safe_exec.py"""

import os.path
import random
import unittest

from capa.safe_exec import safe_exec
from codejail.safe_exec import SafeExecException


class TestSafeExec(unittest.TestCase):
    def test_set_values(self):
        g = {}
        safe_exec("a = 17", g)
        self.assertEqual(g['a'], 17)

    def test_division(self):
        g = {}
        # Future division: 1/2 is 0.5.
        safe_exec("a = 1/2", g)
        self.assertEqual(g['a'], 0.5)

    def test_assumed_imports(self):
        g = {}
        # Math is always available.
        safe_exec("a = int(math.pi)", g)
        self.assertEqual(g['a'], 3)

    def test_random_seeding(self):
        g = {}
        r = random.Random(17)
        rnums = [r.randint(0, 999) for _ in xrange(100)]

        # Without a seed, the results are unpredictable
        safe_exec("rnums = [random.randint(0, 999) for _ in xrange(100)]", g)
        self.assertNotEqual(g['rnums'], rnums)

        # With a seed, the results are predictable
        safe_exec("rnums = [random.randint(0, 999) for _ in xrange(100)]", g, random_seed=17)
        self.assertEqual(g['rnums'], rnums)

    def test_random_is_still_importable(self):
        g = {}
        r = random.Random(17)
        rnums = [r.randint(0, 999) for _ in xrange(100)]

        # With a seed, the results are predictable even from the random module
        safe_exec(
            "import random\n"
            "rnums = [random.randint(0, 999) for _ in xrange(100)]\n",
            g, random_seed=17)
        self.assertEqual(g['rnums'], rnums)

    def test_python_lib(self):
        pylib = os.path.dirname(__file__) + "/test_files/pylib"
        g = {}
        safe_exec(
            "import constant; a = constant.THE_CONST",
            g, python_path=[pylib]
        )

    def test_raising_exceptions(self):
        g = {}
        with self.assertRaises(SafeExecException) as cm:
            safe_exec("1/0", g)
        self.assertIn("ZeroDivisionError", cm.exception.message)


class DictCache(object):
    """A cache implementation over a simple dict, for testing."""

    def __init__(self, d):
        self.cache = d

    def get(self, key):
        # Actual cache implementations have limits on key length
        assert len(key) <= 250
        return self.cache.get(key)

    def set(self, key, value):
        # Actual cache implementations have limits on key length
        assert len(key) <= 250
        self.cache[key] = value


class TestSafeExecCaching(unittest.TestCase):
    """Test that caching works on safe_exec."""

    def test_cache_miss_then_hit(self):
        g = {}
        cache = {}

        # Cache miss
        safe_exec("a = int(math.pi)", g, cache=DictCache(cache))
        self.assertEqual(g['a'], 3)
        # A result has been cached
        self.assertEqual(cache.values()[0], (None, {'a': 3}))

        # Fiddle with the cache, then try it again.
        cache[cache.keys()[0]] = (None, {'a': 17})

        g = {}
        safe_exec("a = int(math.pi)", g, cache=DictCache(cache))
        self.assertEqual(g['a'], 17)

    def test_cache_large_code_chunk(self):
        # Caching used to die on memcache with more than 250 bytes of code.
        # Check that it doesn't any more.
        code = "a = 0\n" + ("a += 1\n" * 12345)

        g = {}
        cache = {}
        safe_exec(code, g, cache=DictCache(cache))
        self.assertEqual(g['a'], 12345)

    def test_cache_exceptions(self):
        # Used to be that running code that raised an exception didn't cache
        # the result.  Check that now it does.
        code = "1/0"
        g = {}
        cache = {}
        with self.assertRaises(SafeExecException):
            safe_exec(code, g, cache=DictCache(cache))

        # The exception should be in the cache now.
        self.assertEqual(len(cache), 1)
        cache_exc_msg, cache_globals = cache.values()[0]
        self.assertIn("ZeroDivisionError", cache_exc_msg)

        # Change the value stored in the cache, the result should change.
        cache[cache.keys()[0]] = ("Hey there!", {})

        with self.assertRaises(SafeExecException):
            safe_exec(code, g, cache=DictCache(cache))

        self.assertEqual(len(cache), 1)
        cache_exc_msg, cache_globals = cache.values()[0]
        self.assertEqual("Hey there!", cache_exc_msg)

        # Change it again, now no exception!
        cache[cache.keys()[0]] = (None, {'a': 17})
        safe_exec(code, g, cache=DictCache(cache))
        self.assertEqual(g['a'], 17)

    def test_unicode_submission(self):
        """ Check that using non-ASCII unicode does not raise an encoding error """
    
        # Try several non-ASCII unicode characters
        for code in [129, 500, 2**8 - 1, 2**16 - 1]:

            code_with_unichr = unicode("# ") + unichr(code)

            try:
                g = {}
                cache = {}
                safe_exec(code_with_unichr, g, cache=DictCache(cache))

            except UnicodeEncodeError:
                self.fail("Tried executing code with non-ASCII unicode: {0}".format(code))