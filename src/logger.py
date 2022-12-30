from typing import TextIO

SUCCESS_SYMBOL = '✔️'
FAILURE_SYMBOL = '❌'
INFO_SYMBOL = 'ℹ️'

# Exception base class implementation used to raise logger utility related exceptions
class LoggerException(Exception):
    def __init__(self, message: str = "Unexpected logger utility failure."):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

# Logging utility class used to send notifications to specified output stream
class Logger:
    def __init__(self, stream: TextIO, verboseMode: bool):
        if stream == None:
            raise LoggerException("Provided stream instance is not initialized.")

        if not stream.writable:
            raise LoggerException("Provided stream is not writable.")

        self.stream = stream
        self.verboseMode = verboseMode

    # Log success message to the output stream
    def log_success(self, message: str) -> None:
        self.stream.write("[ {} ] {}\n".format(SUCCESS_SYMBOL, message.strip()))

    # Log failure message to the output stream
    def log_failure(self, message: str) -> None:
        self.stream.write("[ {} ] {}\n".format(FAILURE_SYMBOL, message.strip()))

    # Log info message to the output stream
    def log_info(self, message: str) -> None:
        self.stream.write("[ {} ] {}\n".format(INFO_SYMBOL, message.strip()))

    # Log info message to the output stream, but the message will only be logged if the logger is in verbose mode
    def log_verbose(self, message: str) -> None:
        if not self.verboseMode: return
        self.stream.write("[ {} ] {}\n".format(INFO_SYMBOL, message.strip()))

    # Log error (failure) exception message to the output stream
    def log_error(self, exception: Exception) -> None:
        if hasattr(exception, 'message'):
            self.stream.write("[ {} ] {}\n".format(FAILURE_SYMBOL, exception.message.strip()))
            return

        self.stream.write("[ {} ] {}\n".format(FAILURE_SYMBOL, str(exception)))

__all__ = [ 'LoggerException', 'Logger' ]