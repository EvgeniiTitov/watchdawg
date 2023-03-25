class Config:
    LOGGER_VERBOSE = True
    LOGGER_FORMAT = (
        "%(asctime)s %(name)s %(levelname)s %(lineno)s: %(message)s"
    )

    SERVER_PORT = 9000
    SERVER_HOST = "192.168.1.104"

    STRUCT_SIZE_FORMAT = ">L"
    JPEG_QUALITY = 95