class EnhancedTestValidator:
    def __init__(self, current_object, errors, parser_name, prev_object):
        self.error_type = parser_name + f" - Test Enhanced Validation Error"
        self.errors = errors

    def validate(self):
        return True
