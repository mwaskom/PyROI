__all__ = ["InitError", "SetupError", "PreprocessError"]

class InitError(Exception):

    def __init__(self, component):
        self.comp = component
    
    def __str__(self):
        return "%s not initialized" % self.comp

class SetupError(Exception):

    def __init__(self, msg=None):
        
        self.msg = msg

    def __str__(self):

        if self.msg is None:
            return "Setup module has not been imported."
        else:
            return self.msg

class PreprocessError(Exception):

    def __init__(self, file):
        self.file = file

    def __str__(self):
        return "%s does not exist" % self.file

