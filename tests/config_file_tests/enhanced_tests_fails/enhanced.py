class EnhancedTestValidator:
    def __init__(self):
        self.name = "Test Enhanced Validator"

    def validate(self, current_object, errors, parser_name, prev_object):
        errors.append({"Error type": "Test Error"})
        return False
