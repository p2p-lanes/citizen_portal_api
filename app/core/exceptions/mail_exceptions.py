from fastapi import HTTPException, status


class InvalidMail(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, 'Invalid mail', None)


class RejectedMail(HTTPException):
    def __init__(self, reason):
        super().__init__(
            status.HTTP_404_NOT_FOUND, f'Mail rejected. Reject reason: {reason}', None
        )


class ErrorMail(HTTPException):
    def __init__(self, detail=None):
        msg = 'An error occurred when sending the mail.'
        if detail:
            msg = f'{msg} Error detail: {detail}'
        super().__init__(status.HTTP_404_NOT_FOUND, msg, None)
