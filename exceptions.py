__all__ = ["InitError", "SetupError", "PreprocessError"]

class InitError(Exception):

    def __init__(self, component):
        self.comp = component
    
    def __str__(self):
        return "%s not initialized" % self.comp

class SetupError(Exception):

    def __str__(self):
        return "Setup module has not been imported."

class PreprocessError(Exception):

    def __init__(self, file):
        self.file = file

    def __str__(self):
        return "%s does not exist" % self.file

