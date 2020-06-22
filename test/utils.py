import os
import tempfile


class MockDir:
    def __init__(self):
        self._directory = tempfile.TemporaryDirectory()
        self.path = self._directory.name

    def __del__(self):
        self._directory._rmtree(self.path)

    def add_file(self, files, content="\n"):
        if not isinstance(files, list):
            files = [files]

        for file in files:
            with open(os.path.join(self.path, file), "w") as f:
                f.write(content)

    def remove_file(self, files):
        if not isinstance(files, list):
            files = [files]

        for file in files:
            os.remove(os.path.join(self.path, file))
