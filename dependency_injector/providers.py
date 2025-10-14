class Provider:
    def __init__(self, callable_=None, *args, **kwargs):
        self._callable = callable_
        self._args = args
        self._kwargs = kwargs

    def __call__(self, *args, **kwargs):
        if self._callable is None:
            return None
        return self._callable(*(self._args + args), **(dict(self._kwargs, **kwargs)))


class Factory(Provider):
    pass


class Callable(Factory):
    pass


class Singleton(Provider):
    def __init__(self, callable_=None, *args, **kwargs):
        super().__init__(callable_, *args, **kwargs)
        self._instance_created = False
        self._instance = None

    def __call__(self, *args, **kwargs):
        if not self._instance_created:
            self._instance = super().__call__(*args, **kwargs)
            self._instance_created = True
        return self._instance


class Configuration:
    def __init__(self, **values):
        self._values = {}
        if values:
            self.from_dict(values)

    def from_dict(self, mapping):
        def _merge(d, u):
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = _merge(d.get(k, {}), v)
                else:
                    d[k] = v
            return d

        _merge(self._values, mapping)

    def __getattr__(self, item):
        v = self._values.get(item)
        if isinstance(v, dict):
            cfg = Configuration()
            cfg._values = v
            return cfg
        return v

    def __getitem__(self, item):
        return self._values[item]

    def get(self, item, default=None):
        return self._values.get(item, default)


class Resource(Factory):
    pass
