import random, logging, time

from pydoover.docker import Application, run_app
from pydoover.config import Schema


class SampleSimulator(Application):
    def setup(self):
        self.last_slow_update = time.time()

        self.loop_target_period = 1

        self.disappearing_value = random.randint(1, 100)
        self.set_tag("disappearing_value", self.disappearing_value)

    def main_loop(self):
        # logging.info("Mainloop is running")
        self.set_tag("random_value", random.randint(1, 100))
        self.set_tag("random_value_2", random.randint(1, 100))

        ## Every 20 seconds, update a slow random value
        if time.time() - self.last_slow_update > 20:
            self.set_tag("slow_random_value", random.randint(1, 100))
            if self.disappearing_value:
                self.disappearing_value = None
            else:
                self.disappearing_value = random.randint(1, 100)
            self.set_tag("disappearing_value", self.disappearing_value)
            self.last_slow_update = time.time()


def main():
    """Run the sample simulator application."""
    run_app(SampleSimulator(config=Schema()))


if __name__ == "__main__":
    main()
