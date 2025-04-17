from enum import Enum, auto
from typing import Dict, Any


class ScreenState(Enum):
    """Represents the possible states of the SelectAlarmScreen"""
    IDLE = auto()           # No alarm selected, not recording/playing
    RECORDING = auto()      # Currently recording
    PLAYING = auto()        # Currently playing audio
    ALARM_SELECTED = auto() # Alarm selected but not playing


BUTTON_STATES: Dict[ScreenState, Dict[str, Dict[str, Any]]] = {
        ScreenState.IDLE: {
            "start_recording": {"active": True, "enabled": True, "text": "Start recording"},
            "stop_recording": {"active": False, "enabled": False},
            "play": {"active": False, "enabled": False},
            "stop": {"active": False, "enabled": False},
            "rename": {"active": False, "enabled": False},
            "delete": {"active": False, "enabled": False},
            "save": {"active": True, "enabled": True},
            "deselect": {"active": False, "enabled": False}
        },
        ScreenState.RECORDING: {
            "start_recording": {"active": False, "enabled": False, "text": "Recording..."},
            "stop_recording": {"active": True, "enabled": True},
            "play": {"active": False, "enabled": False},
            "stop": {"active": False, "enabled": False},
            "rename": {"active": False, "enabled": False},
            "delete": {"active": False, "enabled": False},
            "save": {"active": False, "enabled": False},
            "deselect": {"active": False, "enabled": False}
        },
        ScreenState.PLAYING: {
            "start_recording": {"active": False, "enabled": False, "text": "Start recording"},
            "stop_recording": {"active": False, "enabled": False},
            "play": {"active": False, "enabled": False},
            "stop": {"active": True, "enabled": True},
            "rename": {"active": False, "enabled": False},
            "delete": {"active": False, "enabled": False},
            "save": {"active": False, "enabled": False},
            "deselect": {"active": False, "enabled": False}
        },
        ScreenState.ALARM_SELECTED: {
            "start_recording": {"active": True, "enabled": True, "text": "Start recording"},
            "stop_recording": {"active": False, "enabled": False},
            "play": {"active": True, "enabled": True},
            "stop": {"active": False, "enabled": False},
            "rename": {"active": True, "enabled": True},
            "delete": {"active": True, "enabled": True},
            "save": {"active": True, "enabled": True},
            "deselect": {"active": True, "enabled": True}
        }
    }
