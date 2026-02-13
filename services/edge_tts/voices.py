"""Voice shortcuts."""

VOICE_SHORTCUTS = {
    # English - Female
    "ana": "en-US-AnaNeural",
    "aria": "en-US-AriaNeural",
    "jenny": "en-US-JennyNeural",
    "ava": "en-US-AvaNeural",
    "emma": "en-GB-SoniaNeural",
    
    # English - Male
    "guy": "en-US-GuyNeural",
    "andrew": "en-US-AndrewNeural",
    "brian": "en-US-BrianNeural",
    
    # Asian - Female
    "nanami": "ja-JP-NanamiNeural",
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",
    "sunhi": "ko-KR-SunHiNeural",
    
    # Spanish/Portuguese
    "dalia": "es-MX-DaliaNeural",
    "francisca": "pt-BR-FranciscaNeural",
}


def resolve_voice(voice: str) -> str:
    """Resolve voice shortcut to full voice ID."""
    if not voice:
        return voice
    return VOICE_SHORTCUTS.get(voice.lower(), voice)
