class __CarId:
    def __init__(self):
        id = None

    def get(self):
        return self.id
    
    def set(self, id):
        self.id = id

carId = __CarId()

def getCarId():
    return carId.get()

def setCarId(id):
    carId.set(id)