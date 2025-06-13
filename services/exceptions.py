class StorageBackendError(Exception):
    NOT_FOUND = "Specified storage backend does not exist."
    NOT_CONFIGURED = "No valid configuration found for storage backend."

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
