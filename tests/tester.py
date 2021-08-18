import time
from threading import Thread


class Test:
    def __init__(self, func, *args):
        self.func = func
        self.value = args
        self.completed = None
        self.time = 0
        self.result = None
        self.exception = None

    async def run(self):
        start = time.time()

        try:
            self.result = await self.func()
        except Exception as e:
            self.exception = e.__class__.__name__ + ": " + str(e)

        self.time = (time.time() - start) * 1000
        self.completed = any(self.result == val for val in self.value) and not self.exception


class Tester:
    def __init__(self):
        self.tests = []

        self._thread = Thread(target=self._handle_ui)

    def _handle_ui(self):
        done_tests = []

        while True:
            done = True

            for test in self.tests:
                if test in done_tests:
                    continue

                flush = False

                if test.completed:
                    status_string = f"✅ Passed. {test.time}ms"
                elif test.completed is None:
                    flush = True
                    done = False
                    status_string = "🕒 Running.."
                else:
                    status_string = f"❌ Failed. {test.time}ms"

                if flush:
                    print(f"\rRunning test '{test.func.__name__}' - {status_string}", end="", flush=True)
                else:
                    done_tests.append(test)
                    print(f"\rRunning test '{test.func.__name__}' - {status_string}")

            if done:
                break

            time.sleep(0.05)

        failed = [x for x in self.tests if not x.completed]
        failed_str = "\n".join([f"Test '{x.func.__name__}' failed, " + (f"{x.exception} was raised." if x.exception else f"expected {x.value}, got {x.result}.")
                                for x in failed])
        print(f"---------------\nDone, ({len(self.tests) - len(failed)}/{len(self.tests)}) tests have passed.\n" + failed_str)

    def add_test(self, function, *args):
        self.tests.append(Test(function, *args))

    async def run(self):
        print(f'Running {len(self.tests)} test(s).\n---------------')

        self._thread.start()

        for test in self.tests:
            await test.run()
