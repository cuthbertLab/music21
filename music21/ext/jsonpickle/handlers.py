class BaseHandler(object):
    """
    Abstract base class for handlers.
    """
    def __init__(self, base):
        """
        Initialize a new handler to handle `type`.

        :Parameters:
          - `base`: reference to pickler/unpickler

        """
        self._base = base

    def flatten(self, obj, data):
        """
        Flatten `obj` into a json-friendly form.

        :Parameters:
          - `obj`: object of `type`

        """
        raise NotImplementedError("Abstract method.")

    def restore(self, obj):
        """
        Restores the `obj` to `type`

        :Parameters:
          - `object`: json-friendly object

        """
        raise NotImplementedError("Abstract method.")


class Registry(object):
    REGISTRY = {}

    def register(self, cls, handler):
        """
        Register handler.

        :Parameters:
          - `cls`: Object class
          - `handler`: `BaseHandler` subclass

        """
        self.REGISTRY[cls] = handler
        return handler

    def unregister(self, cls):
        """
        Unregister hander.

        :Parameters:
          - `cls`: Object class
        """
        if cls in self.REGISTRY:
            del self.REGISTRY[cls]

    def get(self, cls):
        """
        Get the customer handler for `obj` (if any)

        :Parameters:
          - `cls`: class to handle

        """
        return self.REGISTRY.get(cls, None)


registry = Registry()
