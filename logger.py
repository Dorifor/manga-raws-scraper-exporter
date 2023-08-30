def log(*message: str) -> None:
    if not __debug__:
        print(message)