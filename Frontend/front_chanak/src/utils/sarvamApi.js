/**
 * Sarvam AI API Utilities
 * Handles Text-to-Speech (TTS) and Speech-to-Text (STT) API calls
 * Supports all Indian languages offered by Sarvam AI
 */

const SARVAM_API_KEY = import.meta.env.VITE_SARVAM_API_KEY || "sk_5j1nftps_Cat40uT2j5qFtBHB53FGCq33";

// STT endpoints from Sarvam docs (we keep these fixed to avoid 404s)
const SARVAM_STT_TRANSCRIBE_URL = "https://api.sarvam.ai/speech-to-text";
const SARVAM_STT_TRANSLATE_URL =
  "https://api.sarvam.ai/speech-to-text-translate";

// TTS endpoint (keep fixed; env can override if explicitly needed later)
const SARVAM_TTS_API_URL = "https://api.sarvam.ai/text-to-speech";

/**
 * Supported Indian languages with their BCP-47 codes
 */
export const SUPPORTED_LANGUAGES = {
  HINDI: { code: "hi-IN", name: "Hindi", nativeName: "हिन्दी" },
  BENGALI: { code: "bn-IN", name: "Bengali", nativeName: "বাংলা" },
  KANNADA: { code: "kn-IN", name: "Kannada", nativeName: "ಕನ್ನಡ" },
  MALAYALAM: { code: "ml-IN", name: "Malayalam", nativeName: "മലയാളം" },
  MARATHI: { code: "mr-IN", name: "Marathi", nativeName: "मराठी" },
  ODIA: { code: "od-IN", name: "Odia", nativeName: "ଓଡ଼ିଆ" },
  PUNJABI: { code: "pa-IN", name: "Punjabi", nativeName: "ਪੰਜਾਬੀ" },
  TAMIL: { code: "ta-IN", name: "Tamil", nativeName: "தமிழ்" },
  TELUGU: { code: "te-IN", name: "Telugu", nativeName: "తెలుగు" },
  ENGLISH: { code: "en-IN", name: "English (India)", nativeName: "English" },
  GUJARATI: { code: "gu-IN", name: "Gujarati", nativeName: "ગુજરાતી" },
};

/**
 * Available TTS speakers by language
 * bulbul:v2 model speakers
 */
export const AVAILABLE_SPEAKERS = {
  FEMALE: ["anushka", "manisha", "vidya", "arya"],
  MALE: ["abhilash", "karun", "hitesh"],
};

/**
 * Default speakers for each language (customize as needed)
 */
export const DEFAULT_SPEAKERS = {
  "hi-IN": "manisha",
  "bn-IN": "anushka",
  "kn-IN": "vidya",
  "ml-IN": "arya",
  "mr-IN": "manisha",
  "od-IN": "anushka",
  "pa-IN": "vidya",
  "ta-IN": "arya",
  "te-IN": "manisha",
  "en-IN": "anushka",
  "gu-IN": "vidya",
};

/**
 * Get all supported language codes
 * @returns {string[]} Array of language codes
 */
export const getSupportedLanguageCodes = () => {
  return Object.values(SUPPORTED_LANGUAGES).map((lang) => lang.code);
};

/**
 * Get language info by code
 * @param {string} code - Language code (e.g., "hi-IN")
 * @returns {Object|null} Language info object or null
 */
export const getLanguageInfo = (code) => {
  return (
    Object.values(SUPPORTED_LANGUAGES).find((lang) => lang.code === code) ||
    null
  );
};

/**
 * Get default speaker for a language
 * @param {string} languageCode - Language code (e.g., "hi-IN")
 * @returns {string} Default speaker name
 */
export const getDefaultSpeaker = (languageCode) => {
  return DEFAULT_SPEAKERS[languageCode] || "manisha";
};

/**
 * Decode base64 audio string to Blob
 * @param {string} base64Audio - Base64 encoded audio string
 * @returns {Blob} Audio blob
 */
const base64ToBlob = (base64Audio) => {
  const binaryString = atob(base64Audio);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return new Blob([bytes], { type: "audio/wav" });
};

/**
 * Transcribe audio using Sarvam AI Speech-to-Text API
 * @param {Blob} audioBlob - Audio blob to transcribe
 * @param {Object} options - Transcription options
 * @param {"transcribe"|"translate"} options.mode - "transcribe" (Saarika) or "translate" (Saaras) (default: "transcribe")
 * @param {string} options.languageCode - Language code (BCP-47) or "unknown" for auto-detection (default: "unknown")
 * @returns {Promise<Object>} Transcription result with transcript, detected language and request id
 */
export const transcribeAudio = async (audioBlob, options = {}) => {
  const { mode = "transcribe", languageCode = "unknown" } = options;

  const isTranslate = mode === "translate";
  const endpoint = isTranslate
    ? SARVAM_STT_TRANSLATE_URL
    : SARVAM_STT_TRANSCRIBE_URL;
  const model = isTranslate ? "saaras:v2.5" : "saarika:v2.5";

  try {
    if (!SARVAM_API_KEY) {
      throw new Error("Sarvam API key not configured");
    }

    // Create FormData and append the audio file
    const formData = new FormData();
    formData.append("file", audioBlob, "audio.wav");
    formData.append("model", model);
    // language_code only for transcription mode
    if (!isTranslate) {
      formData.append("language_code", languageCode);
    }

    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "api-subscription-key": SARVAM_API_KEY,
        // Don't set Content-Type - browser will set it with boundary
      },
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("STT API Error Response:", errorText);
      throw new Error(`Transcription failed: ${response.status}`);
    }

    const data = await response.json();
    console.log("STT Response:", data); // Debug log

    return {
      transcript: data.transcript || "",
      detectedLanguage: data.language_code || null,
      requestId: data.request_id || null,
    };
  } catch (error) {
    console.error("Sarvam STT API error:", error);
    throw error;
  }
};

/**
 * Generate speech using Sarvam AI Text-to-Speech API
 * @param {string} text - Text to convert to speech
 * @param {Object} options - TTS options
 * @param {string} options.languageCode - Target language code (default: "hi-IN")
 * @param {string} options.speaker - Speaker name (default: auto-selected based on language)
 * @param {string} options.model - Model to use (default: "bulbul:v2")
 * @param {number} options.pitch - Voice pitch -0.75 to 0.75 (default: 0)
 * @param {number} options.pace - Speech speed 0.5 to 2.0 (default: 1.0)
 * @param {number} options.loudness - Audio loudness 0.3 to 3.0 (default: 1.0)
 * @returns {Promise<Blob>} Audio blob
 */
export const generateSpeech = async (text, options = {}) => {
  const {
    languageCode = "hi-IN",
    speaker = null,
    model = "bulbul:v2",
    pitch = 0,
    pace = 1.0,
    loudness = 1.0,
  } = options;

  try {
    if (!SARVAM_API_KEY) {
      throw new Error("Sarvam API key not configured");
    }

    // Validate language code
    const supportedCodes = getSupportedLanguageCodes();
    if (!supportedCodes.includes(languageCode)) {
      console.warn(
        `Language ${languageCode} not in supported list. Attempting anyway...`
      );
    }

    // Auto-select speaker if not provided
    const selectedSpeaker = speaker || getDefaultSpeaker(languageCode);

    const requestBody = {
      text: text,
      target_language_code: languageCode,
      speaker: selectedSpeaker,
      model: model,
    };

    // Add optional parameters if they differ from defaults
    if (pitch !== 0) requestBody.pitch = pitch;
    if (pace !== 1.0) requestBody.pace = pace;
    if (loudness !== 1.0) requestBody.loudness = loudness;

    const response = await fetch(SARVAM_TTS_API_URL, {
      method: "POST",
      headers: {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("TTS API Error:", errorText);
      throw new Error(`${response.status}: ${errorText}`);
    }

    const data = await response.json();
    console.log("TTS Response:", data); // Debug log

    // Response has 'audios' array with base64 audio strings
    if (
      !data.audios ||
      !Array.isArray(data.audios) ||
      data.audios.length === 0
    ) {
      throw new Error("No audio data in Sarvam API response");
    }

    // Decode base64 audio string and return blob
    const base64Audio = data.audios[0];
    return base64ToBlob(base64Audio);
  } catch (error) {
    console.error("Sarvam TTS API error:", error);
    throw error;
  }
};

/**
 * Play audio blob with optional callbacks
 * @param {Blob} audioBlob - Audio blob to play
 * @param {Object} options - Options object
 * @param {Function} options.onPlay - Callback when audio starts playing
 * @param {Function} options.onEnd - Callback when audio finishes
 * @param {Function} options.onError - Callback if error occurs
 * @returns {Audio} Audio element
 */
export const playAudio = (audioBlob, options = {}) => {
  const { onPlay, onEnd, onError } = options;

  const audioUrl = URL.createObjectURL(audioBlob);
  const audio = new Audio(audioUrl);

  if (onPlay) {
    audio.onplay = onPlay;
  }

  if (onEnd) {
    audio.onended = () => {
      onEnd();
      URL.revokeObjectURL(audioUrl);
    };
  }

  if (onError) {
    audio.onerror = (error) => {
      onError(error);
      URL.revokeObjectURL(audioUrl);
    };
  } else {
    audio.onerror = () => {
      URL.revokeObjectURL(audioUrl);
    };
  }

  audio.play();
  return audio;
};

/**
 * Convert text to speech and play it
 * @param {string} text - Text to convert to speech
 * @param {Object} options - Options object (combines playAudio and generateSpeech options)
 * @param {Function} options.onPlay - Callback when audio starts
 * @param {Function} options.onEnd - Callback when audio ends
 * @param {string} options.languageCode - Target language code (default: "hi-IN")
 * @param {string} options.speaker - Speaker name (default: auto-selected)
 * @param {number} options.pitch - Voice pitch (default: 0)
 * @param {number} options.pace - Speech speed (default: 1.0)
 * @param {number} options.loudness - Audio loudness (default: 1.0)
 * @returns {Promise<Audio>} Audio element
 */
export const textToSpeechAndPlay = async (text, options = {}) => {
  const { onPlay, onEnd, onError, ...ttsOptions } = options;

  try {
    const audioBlob = await generateSpeech(text, ttsOptions);
    return playAudio(audioBlob, { onPlay, onEnd, onError });
  } catch (error) {
    console.error("Text to speech error:", error);
    throw error;
  }
};

/**
 * Detect language from text (simple heuristic - for production use a proper detection library)
 * @param {string} text - Text to analyze
 * @returns {string} Detected language code or "hi-IN" as default
 */
export const detectLanguageFromText = (text) => {
  // Simple Unicode range detection for Indian languages
  const languageRanges = {
    "hi-IN": /[\u0900-\u097F]/, // Devanagari (Hindi/Marathi)
    "bn-IN": /[\u0980-\u09FF]/, // Bengali
    "gu-IN": /[\u0A80-\u0AFF]/, // Gujarati
    "pa-IN": /[\u0A00-\u0A7F]/, // Gurmukhi (Punjabi)
    "ta-IN": /[\u0B80-\u0BFF]/, // Tamil
    "te-IN": /[\u0C00-\u0C7F]/, // Telugu
    "kn-IN": /[\u0C80-\u0CFF]/, // Kannada
    "ml-IN": /[\u0D00-\u0D7F]/, // Malayalam
    "od-IN": /[\u0B00-\u0B7F]/, // Odia
    "en-IN": /^[a-zA-Z0-9\s.,!?]+$/, // English
  };

  for (const [lang, pattern] of Object.entries(languageRanges)) {
    if (pattern.test(text)) {
      return lang;
    }
  }

  return "hi-IN"; // Default to Hindi
};
