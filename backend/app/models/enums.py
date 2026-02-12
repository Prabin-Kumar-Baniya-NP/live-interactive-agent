from enum import Enum, unique


@unique
class AgentModality(str, Enum):
    AUDIO_ONLY = "audio_only"
    AUDIO_CAMERA = "audio_camera"
    AUDIO_SCREENSHARE = "audio_screenshare"


@unique
class PanelType(str, Enum):
    SLIDE_PRESENTER = "slide_presenter"
    NOTEPAD = "notepad"
    CODING_IDE = "coding_ide"
    WHITEBOARD = "whiteboard"
    DOCUMENT_VIEWER = "document_viewer"
