import pycom
import time


class CriticalCarSequence:
    def sequense(self):
        return {
            "name": "", #Name of sequense
            "criticality": 0.0, #Score between 0 and 1
            "permanend_damage": True, #Should go in permanend crash mode
            "danger": 0.9, #How dangeroes is the situation on the track
            "conditionSequence": 
            [ #sequential condition list
                {
                    "condition": "abs(sensors['Accelerometer']['roll']) > 120", #condition
                    "min_duration": -1, #min duration (in ms) the condition should be True (-1 is from first measurement)
                    "noiseCount": 0, #amount of incorrect measures allowed over the time period, NOT IMPLEMENTED YET
                    "state": False, #State of this sequence will be automaticly set True when condition is passed,
                    "first": None #Placeholder for keeping first sensor_data for the current condition min_duration check
                 },
            ]
        }

#Should not be g_force but speed using gps
class State_NoSpeed(CriticalCarSequence):
    def sequense(self):
        return {
            "criticality": 0.0, "name": "NoSpeed", "permanend_damage": True, "danger": 0.5,
            "conditionSequence": 
            [
                {"condition": "sensors['Accelerometer']['g_force'] > 1.8", "min_duration": -1, "state": False, "noiseCount": 0, "first": None }, #Must have driven
                {"condition": "sensors['Accelerometer']['g_force'] < 1.3", "min_duration": 5000, "state": False, "noiseCount": 50, "first": None }, #Then must be 5 sec standing still
            ]
        }

class Crash_SlightCarFlip(CriticalCarSequence):
    def sequense(self):
        return {
            "criticality": 0.7, "name": "SlightCarFlip", "permanend_damage": True, "danger": 0.8,
            "conditionSequence": 
            [
                {"condition": "abs(sensors['Accelerometer']['roll']) > 80", "min_duration": -1, "state": False, "noiseCount": 0, "first": None },
            ]
        }
    
class Crash_HardCarFlip(CriticalCarSequence):
    def sequense(self):
        return {
            "criticality": 0.9, "name": "HardCarFlip", "permanend_damage": True, "danger": 0.9, "noiseCount": 0,
            "conditionSequence": 
            [
                {"condition": "abs(sensors['Accelerometer']['roll']) > 120", "min_duration": -1, "state": False, "noiseCount": 0, "first": None },
            ]
        }

class CarStateDetection:
    def __init__(self):
        self.crashSequences = []
        self.crashed = False
    
    def add_crash_sequense(self, sequence: CrashSequence):
        self.crashSequences.append(sequence.sequense())

    def check(self, current_sensor_data):
        """
        Checks for crash
        return:
        True by crash
        False by no crashes
        """
        for crashSequence in self.crashSequences:
            try:
                for conditionStep in crashSequence["conditionSequence"]:
                    if conditionStep["state"]: 
                        continue
                    condition = conditionStep["condition"]
                    
                    condition_value = eval(condition, {}, {"sensors": current_sensor_data})

                    if condition_value and conditionStep["first"] == None:
                        print("OVerwrite first")
                        conditionStep["first"] = current_sensor_data["time"]
                        conditionStep["noiseCountDown"] = conditionStep["noiseCount"]
                    elif not condition_value and "noiseCountDown" in conditionStep.keys():
                        if conditionStep["noiseCountDown"] == 0:
                            conditionStep["first"] = None
                        else:
                            conditionStep["noiseCountDown"] -= 1

                    if condition_value and (conditionStep["min_duration"] == -1 or (conditionStep["first"] is not None and conditionStep["min_duration"] < abs(conditionStep["first"] - current_sensor_data["time"]))):
                        conditionStep["state"] = True

                    if not conditionStep["state"]:
                        break #Stop loop on not completed contition
            except:
                print(crashSequence["name"], " failed to check")
            if self.crashSequences[-1]["conditionSequence"][-1]["state"]:
                return True
        return False
    
    def checkAndProcess(self, current_sensor_data):
        if self.crashed:
            return
        if self.check(current_sensor_data):
            pycom.heartbeat(False)
            while True:
                self.crashed = True
                pycom.rgbled(0xFF0000)  # Red
                time.sleep(1)
                pycom.rgbled(0x000000)
                time.sleep(1)
                print("CRASH!")
                