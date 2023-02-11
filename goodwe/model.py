from .inverter import Inverter

# Serial number tags to identify inverter type
ET_MODEL_TAGS = ["ETU", "EHU", "BTU", "BHU", "HSB"]
ES_MODEL_TAGS = ["ESU", "EMU", "BPU", "BPS"]
DT_MODEL_TAGS = ["DTU", "MSU", "MST", "DTN", "DSN", "PSB", "PSC"]


def isSinglePhaseDT(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in ["DSN", "MSU", "MST", "PSB", "PSC"])


def is3PVstringDT(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in ["MSU", "MST", "PSC"])


def isSinglePhaseET(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in ["EHU", "EHR"])


def is4PVstringET(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in ["HSB"])
