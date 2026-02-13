"""Text to Speech — API documentation and examples.

Auto-loaded by the service loader for the tester Docs tab.
"""

NOTES = [
    "Returns audio/mpeg binary — save the response as an .mp3 file",
    "Use <code>list_voices: true</code> to discover all available voices before generating",
    "Rate, pitch, and volume accept percentage strings like <code>\"+50%\"</code> or <code>\"-20%\"</code>",
]

EXAMPLES = [
    {
        "title": "Basic Text to Speech",
        "description": "Convert text to speech using the default English voice",
        "body": {"text": "Hello, welcome to the API!", "voice": "en-US-JennyNeural"},
    },
    {
        "title": "Custom Voice & Speed",
        "description": "Use a male voice with faster speed and higher pitch",
        "body": {"text": "Breaking news: AI is amazing!", "voice": "en-US-GuyNeural", "rate": "+30%", "pitch": "+10Hz"},
    },
    {
        "title": "Multilingual — Spanish",
        "description": "Generate speech in Spanish",
        "body": {"text": "Hola, bienvenido a nuestro servicio", "voice": "es-ES-ElviraNeural"},
    },
    {
        "title": "Multilingual — Japanese",
        "description": "Generate speech in Japanese with slow speed",
        "body": {"text": "こんにちは、世界", "voice": "ja-JP-NanamiNeural", "rate": "-20%"},
    },
    {
        "title": "Multilingual — French",
        "description": "Generate speech in French with adjusted volume",
        "body": {"text": "Bonjour le monde, bienvenue!", "voice": "fr-FR-DeniseNeural", "volume": "+20%"},
    },
    {
        "title": "List All Voices",
        "description": "Get a list of all available voices grouped by locale",
        "body": {"list_voices": True},
    },
]
