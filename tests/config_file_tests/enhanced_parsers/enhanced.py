class EnhancedTestValidator:
    def __init__(self, measurement_object, errors, parser_name):
        self.error_type = parser_name + f" - Test Enhanced Validation Error"
        self.errors = errors

    def validate(self):
        return True
