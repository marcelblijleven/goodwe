"""Constants identifying inverter type/model."""

from .inverter import Inverter

PLATFORM_105_MODELS = ("ESU", "EMU", "ESA", "BPS", "BPU", "EMJ", "IJL")
PLATFORM_205_MODELS = ("ETU", "ETL", "ETR", "BHN", "EHU", "BHU", "EHR", "BTU")
PLATFORM_745_LV_MODELS = (
    "ESN",
    "EBN",
    "EMN",
    "SPN",
    "ERN",
    "ESC",
    "HLB",
    "HMB",
    "HBB",
    "EOA",
)
PLATFORM_745_HV_MODELS = (
    "ETT",
    "HTA",
    "HUB",
    "AEB",
    "SPB",
    "CUB",
    "EUB",
    "HEB",
    "ERB",
    "BTT",
    "ETF",
    "ARB",
    "URB",
    "EBR",
    "NAH",  # ESA/EHA-G20
)
PLATFORM_753_MODELS = ("AES", "HHI", "ABP", "EHB", "HSB", "HUA", "CUA")

ET_MODEL_TAGS = (
    PLATFORM_205_MODELS
    + PLATFORM_745_LV_MODELS
    + PLATFORM_745_HV_MODELS
    + PLATFORM_753_MODELS
    # Qianhai
    + ("ETC", "BTC", "BTN")
)
ES_MODEL_TAGS = PLATFORM_105_MODELS
DT_MODEL_TAGS = (
    "DTU",
    "DTS",
    "KMT",
    "MSU",
    "MST",
    "MSC",
    "DSN",
    "DTN",
    "DST",
    "NSU",
    "SSN",
    "SST",
    "SSX",
    "SSY",
    "PSB",
    "PSC",
)

SINGLE_PHASE_MODELS = (
    # DT
    "DSN",
    "DST",
    "NSU",
    "SSN",
    "SST",
    "SSX",
    "SSY",
    "MSU",
    "MST",
    "PSB",
    "PSC",
    # Found on third gen MS
    "MSC",
    # ET
    "EHB",
    "EHU",
    "EHR",
    "HSB",
    # ES Gen 2
    "ESN",
    "EMN",
    "ERN",
    "EBN",
    "HLB",
    "HMB",
    "HBB",
    "SPN",
    "NAH",
)

MPPT3_MODELS = (
    "MSU",
    "MST",
    "PSC",
    "MSC",
    "25KET",
    "29K9ET",
    "25KMT",
    "GW10K-ET20",
    "GW12K-ET20",
    "GW15K-ET20",
)

MPPT4_MODELS = ("DTB", "KMT", "HSB", "EHB", "GW8K-EHA-G20", "GW10K-EHA-G20")

BAT_2_MODELS = ("25KET", "29K9ET")

# Model names that identify the phase even when the serial number does not.
# Newer DNS units ship a serial with none of the SINGLE_PHASE_MODELS tags, so
# the serial match alone reports them as three-phase. That is not cosmetic:
# DT then binds grid_export_limit to the three-phase register 40336 (percent)
# instead of the single-phase 40328 (watts), a register these units ignore, so
# the export limit silently stops working. GoodWe names the product "DNS" where
# the serial tags use "DSN".
SINGLE_PHASE_MODEL_NAMES = (
    "DNS",
)


def is_single_phase(inverter: Inverter) -> bool:
    model_name = inverter.model_name or ""
    if any(tag in model_name for tag in SINGLE_PHASE_MODEL_NAMES):
        return True
    return any(model in inverter.serial_number for model in SINGLE_PHASE_MODELS)


def is_3_mppt(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in MPPT3_MODELS)


def is_4_mppt(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in MPPT4_MODELS)


def is_2_battery(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in BAT_2_MODELS)


def is_745_platform(inverter: Inverter) -> bool:
    return any(
        model in inverter.serial_number for model in PLATFORM_745_LV_MODELS
    ) or any(model in inverter.serial_number for model in PLATFORM_745_HV_MODELS)


def is_753_platform(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in PLATFORM_753_MODELS)
