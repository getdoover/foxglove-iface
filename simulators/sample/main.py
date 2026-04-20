import logging
import random
import time

from pydoover.docker import Application, run_app
from pydoover.tags import Tag, Tags

log = logging.getLogger(__name__)


class SampleSimulatorTags(Tags):
    random_value = Tag("number", default=None)
    random_value_2 = Tag("number", default=None)
    slow_random_value = Tag("number", default=None)
    disappearing_value = Tag("number", default=None)


class SampleSimulator(Application):
    tags_cls = SampleSimulatorTags
    loop_target_period = 1

    async def setup(self):
        self.last_slow_update = time.time()
        self.disappearing_value = random.randint(1, 100)
        await self.tags.disappearing_value.set(self.disappearing_value)

    async def main_loop(self):
        await self.tags.random_value.set(random.randint(1, 100))
        await self.tags.random_value_2.set(random.randint(1, 100))

        if time.time() - self.last_slow_update > 20:
            await self.tags.slow_random_value.set(random.randint(1, 100))
            self.disappearing_value = (
                None if self.disappearing_value else random.randint(1, 100)
            )
            await self.tags.disappearing_value.set(self.disappearing_value)
            self.last_slow_update = time.time()


def main():
    """Run the sample simulator application."""
    run_app(SampleSimulator())


if __name__ == "__main__":
    main()
