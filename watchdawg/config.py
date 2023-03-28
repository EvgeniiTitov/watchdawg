class Config:

    # Logger
    LOGGER_VERBOSE = True
    LOGGER_FORMAT = (
        "%(asctime)s %(name)s %(levelname)s %(lineno)s: %(message)s"
    )

    # TCPServer / TCPClient
    SERVER_PORT = 9000
    SERVER_HOST = "192.168.1.104"
    STRUCT_SIZE_FORMAT = ">L"
    JPEG_QUALITY = 95
    MODEL_INPUT_WIDTH = 640
    MODEL_INPUT_HEIGHT = 360
    REPORT_STATE_FREQUENCY = 5

    # FeedHandler
    DECODED_FRAMES_QUEUE_SIZE = 1000
    BUILD_BATCH_TIME_WINDOW = 0.1

    # ML
    MODEL_BATCH_SIZE = 64

    # ResultsWriter
    PROCESSED_BATCHES_QUEUE_SIZE = 50
    PROCESSED_FEED_LOCAL_FOLDER = ""
    CLIENT_QUEUE = 100
