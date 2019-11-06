from pint import UnitRegistry


class Singleton(type):
    """
    Define an Instance operation that lets clients access its unique
    instance.
    """

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class UnitConversion(metaclass=Singleton):
    def __init__(self):

        # Initialize pint's unit registry object
        self.unit_reg = UnitRegistry()

        self.metre_per_second = self.unit_reg.metre / self.unit_reg.second

    def get_unit_registry(self):
        return self.unit_reg
