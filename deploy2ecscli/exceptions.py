class TaskFailedException(Exception):
    def __init__(self, task_arn, failed_containers):
        message = '{0} is failed.'
        message = message.format(task_arn)
        
        super().__init__(message, failed_containers)