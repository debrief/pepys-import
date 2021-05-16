from datetime import datetime
import json


class PepysEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


def make_error_response(message: str, http_status_code: str = 500):
    return {
        'error': {
            'message': message
        }
    }, http_status_code
