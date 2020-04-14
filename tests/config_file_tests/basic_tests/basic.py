class BasicTestValidator:
    def __init__(self, parser_name):
        self.name = "Test Basic Validator"
        self.error_type = f"{parser_name} - {self.name} Error"

    def validate(self, measurement, errors):
        return True
