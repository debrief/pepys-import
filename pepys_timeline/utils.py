def make_error_response(message: str, http_status_code: str = 500):
    return {
        'error': {
            'message': message
        }
    }, http_status_code
