from collections import OrderedDict
import os
import logging
import threading

from watchdog.events import PatternMatchingEventHandler

from osfoffline import settings
from osfoffline.exceptions import NodeNotFound


logger = logging.getLogger(__name__)


class ConsolidatedEventHandler(PatternMatchingEventHandler):

    @classmethod
    def _flatten(cls, d, l):
        for x in d.values():
            if isinstance(x, dict):
                cls._flatten(x, l)
            else:
                l.append(x)
        return l

    def __init__(self):
        super().__init__(ignore_patterns=settings.IGNORED_PATTERNS)
        self._event_cache = OrderedDict()
        self.timer = threading.Timer(2, self.flush)
        self.timer.start()
        self.lock = threading.RLock()

    def dispatch(self, event):
        with self.lock:
            if event.is_directory and event.event_type == 'modified':
                return

            src_parent = event.src_path.split(os.path.sep)
            src_parent, src_name = src_parent[:-1], src_parent[-1]
            if not hasattr(event, 'dest_path'):
                dest_parent, dest_name = [None for _ in src_parent], None
            else:
                dest_parent = event.dest_path.split(os.path.sep)
                dest_parent, dest_name = dest_parent[:-1], dest_parent[-1]

            cache = self._event_cache
            for src_seg, dest_seg in zip(src_parent, dest_parent):
                if not isinstance(cache, dict):
                    break
                cache = cache.setdefault((src_seg, dest_seg), OrderedDict())
            else:
                if isinstance(cache, dict):
                    cache[(src_name, dest_name)] = event

            self.timer.cancel()
            self.timer = threading.Timer(2, self.flush)
            self.timer.start()

    def flush(self):
        with self.lock:
            for e in self._flatten(self._event_cache, []):
                try:
                    super().dispatch(e)
                except (NodeNotFound, ) as ex:
                    logger.warning(ex)
                except Exception as ex:
                    logger.exception(ex)
            self._event_cache = OrderedDict()
