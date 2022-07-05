import os


class Paths:
    def __init__(self, project_dir):
        self.project_dir = project_dir

    @property
    def data(self):
        return os.path.join(self.project_dir, "pydeflate", "data")


PATHS = Paths(os.path.dirname(os.path.dirname(__file__)))
