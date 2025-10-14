class DeclarativeContainer:
    def __init__(self, *args, **kwargs):
        pass

    def wire(self, packages=None, modules=None):
        # No-op in shim
        return None
