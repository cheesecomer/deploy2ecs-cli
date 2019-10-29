class DescribeFailedException(Exception):
    def __init__(self, resource_name, failures):
        message = 'Fetch {0} describe failed.'
        message = message.format(resource_name)
        super().__init__(message, failures)