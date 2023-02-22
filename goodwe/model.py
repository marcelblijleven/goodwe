from .inverter import Inverter

# Serial number tags to identify inverter type
ET_MODEL_TAGS = ["ETU", "EHU", "BTU", "BHU", "HSB"]
ES_MODEL_TAGS = ["ESU", "EMU", "BPU", "BPS"]
DT_MODEL_TAGS = ["DTU", "MSU", "MST", "DTN", "DSN", "PSB", "PSC"]

SINGLE_PHASE_MODELS = ["DSN", "MSU", "MST", "PSB", "PSC", "EHU", "EHR", "HSB"]


def is_single_phase(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in SINGLE_PHASE_MODELS)


def is_3_mptt(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in ["MSU", "MST", "PSC"])


def is_4_mptt(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in ["HSB"])
