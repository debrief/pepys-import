from .unit_conversion import UnitConversion

# Initializing Pint's Unit Registry
conversion = UnitConversion()
unit_registry = conversion.getUnitRegistry()
quantity = unit_registry.Quantity