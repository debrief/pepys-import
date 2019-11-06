from .unit_conversion import UnitConversion

# Initializing Pint's Unit Registry
conversion = UnitConversion()
unit_registry = conversion.get_unit_registry()
quantity = unit_registry.Quantity
