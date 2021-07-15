

class InvalidArguments(BaseException):
    
    def __init__(self, *args: object) -> None:
        super().__init__(*args)