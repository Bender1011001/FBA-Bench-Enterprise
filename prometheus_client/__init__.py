class _MetricBase:
    def __init__(self, name, documentation, labelnames=(), registry=None, **kwargs):
        self._name = name
        self._documentation = documentation
        self._labelnames = labelnames
        self._labels = {}

    def labels(self, *args, **kwargs):
        return self

    def inc(self, amount=1):
        return None

    def dec(self, amount=1):
        return None

    def observe(self, amount):
        return None

    def set(self, value):
        return None


class Counter(_MetricBase):
    pass


class Gauge(_MetricBase):
    pass


class Histogram(_MetricBase):
    def __init__(self, name, documentation, labelnames=(), registry=None, buckets=None, **kwargs):
        super().__init__(name, documentation, labelnames, registry, **kwargs)


class CollectorRegistry:
    def __init__(self, auto_describe=False):
        self.auto_describe = auto_describe


def start_http_server(port, addr=""):
    return None
