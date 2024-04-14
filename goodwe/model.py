# Serial number tags to identify inverter type
from .inverter import Inverter

PLATFORM_105_MODELS = ("ESU", "EMU", "ESA", "BPS", "BPU", "EMJ", "IJL")
PLATFORM_205_MODELS = ("ETU", "ETL", "ETR", "BHN", "EHU", "BHU", "EHR", "BTU")
PLATFORM_745_LV_MODELS = ("ESN", "EBN", "EMN", "SPN", "ERN", "ESC", "HLB", "HMB", "HBB", "EOA")
PLATFORM_745_HV_MODELS = ("ETT", "HTA", "HUB", "AEB", "SPB", "CUB", "EUB", "HEB", "ERB", "BTT", "ETF", "ARB", "URB",
                          "EBR")
PLATFORM_753_MODELS = ("AES", "HHI", "ABP", "EHB", "HSB", "HUA", "CUA")

ET_MODEL_TAGS = PLATFORM_205_MODELS + PLATFORM_745_LV_MODELS + PLATFORM_745_HV_MODELS + PLATFORM_753_MODELS + (
    "ETC", "BTC", "BTN")  # Qianhai
ES_MODEL_TAGS = PLATFORM_105_MODELS
DT_MODEL_TAGS = ("DTU", "DTS",
                 "MSU", "MST", "MSC", "DSN", "DTN", "DST", "NSU", "SSN", "SST", "SSX", "SSY",
                 "PSB", "PSC")

SINGLE_PHASE_MODELS = ("DSN", "DST", "NSU", "SSN", "SST", "SSX", "SSY",  # DT
                       "MSU", "MST", "PSB", "PSC",
                       "MSC",  # Found on third gen MS
                       "EHU", "EHR", "HSB",  # ET
                       "ESN", "EMN", "ERN", "EBN", "HLB", "HMB", "HBB", "SPN")  # ES Gen 2

MPPT3_MODELS = ("MSU", "MST", "PSC", "MSC",
                "25KET", "29K9ET")

MPPT4_MODELS = ("HSB",)

BAT_2_MODELS = ("25KET", "29K9ET")


def is_single_phase(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in SINGLE_PHASE_MODELS)


def is_3_mppt(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in MPPT3_MODELS)


def is_4_mppt(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in MPPT4_MODELS)


def is_2_battery(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in BAT_2_MODELS)


def is_745_platform(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in PLATFORM_745_LV_MODELS) or any(
        model in inverter.serial_number for model in PLATFORM_745_HV_MODELS)
