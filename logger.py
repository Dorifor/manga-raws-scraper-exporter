def log(message: str) -> None:
    if __debug__:
        print(message)