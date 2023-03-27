class DawgException(Exception):
    pass


class FeedProcessorStoppedError(DawgException):
    """This exception is raised if there is an attempt to register/submit
    a frame for processing with the stopping/stopped FeedProcessor"""
