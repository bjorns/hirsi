"""
Logs are the main interface for users to interact with the package.
"""
from .event import Event
from .error import UserError
from .filter import Filter, LevelFilter, PROCESSED, TERMINATED
from .format import Format, SimpleFormat
from .level import Level, DEBUG, INFO, NOTICE, WARNING, ERROR
from .drain import Drain, StderrDrain


class Log:
    """
    Base class for log implementations
    """

    def __init__(self):
        pass

    def update(self, new_log):
        pass

    def debug(self, msg: str):
        self.log(DEBUG, msg)

    def info(self, msg: str):
        self.log(INFO, msg)

    def notice(self, msg: str):
        self.log(NOTICE, msg)

    def warning(self, msg: str):
        self.log(WARNING, msg)

    def error(self, msg: str):
        self.log(ERROR, msg)

    def log(self, level: Level, msg: str):
        pass


class LogPipeline(Log):
    """
    LogPipeline is a flexible log implementation. It uses submodules to implement all functionality
    as a pipeline of events that filter and then output events. The process is:

    - A set of filters modify or filter out events based on e.g. level
    - A formatter converts the event into a bytestream (string)
    - A set of writers write the event to some output stream.

    The log pipeline has a set of default settings so:

        LogPipeline("ny-log")

    is equivalent to:

        LogPipeline("my-log", LevelFilter(INFO),  SimpleFormat(), StderrDrain())

    """

    def __init__(self, name: str, *components):
        super(LogPipeline, self).__init__()
        self.name = name
        self.filters = list()
        self.format = None
        self.drains = list()

        for component in components:
            if issubclass(type(component), Filter):
                self.filters.append(component)
            elif issubclass(type(component), Format):
                if self.format is not None:
                    raise UserError(f"A log pipeline cannot have two formats: {self.format} and {component}")
                self.format = component
            elif issubclass(type(component), Drain):
                self.drains.append(component)
            else:
                raise UserError(f"Object {component}({type(component)}) is not a supported component")

        if len(self.filters) == 0:
            self.filters.append(LevelFilter(INFO))

        # If user has supplied no formatter, use a default
        if self.format is None:
            self.format = SimpleFormat()

        # If user has supplied no drain, use stderr as default
        if len(self.drains) == 0:
            self.drains.append(StderrDrain())

    def log(self, level: Level, msg: str):
        event = Event(level, msg)

        for flt in self.filters:
            if flt.process(event) == TERMINATED:
                return

        line = self.format.format(event)
        for drain in self.drains:
            drain.write(line)

    def update(self, new_log):
        assert self.name == new_log.name
        self.filters = new_log.filters
        self.format = new_log.format
        self.drains = new_log.drains

    def __repr__(self) -> str:
        return f"LogPipeline<{self.name}>"
