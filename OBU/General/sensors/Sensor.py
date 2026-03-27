class Sensor():
    def __init__(self, pycoproc):
            self.name = "Sensor"
            raise "Cannot init abstract sensor"

    def get(self):
        raise "Cannot get data from abstract sensor"
