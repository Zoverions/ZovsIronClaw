import type {
  MediaUnderstandingInput,
  MediaUnderstandingProvider,
  MediaUnderstandingResult,
} from "../../types.js";

export const gcaProvider: MediaUnderstandingProvider = {
  id: "gca",
  name: "GCA Local",
  capabilities: ["audio", "image", "video"],

  transcribeAudio: async (
    input: MediaUnderstandingInput,
  ): Promise<MediaUnderstandingResult> => {
    const baseUrl = process.env.GCA_API_URL || "http://gca-service:8000";
    const formData = new FormData();
    const blob = new Blob([input.buffer], { type: input.mime });
    formData.append("file", blob, input.fileName);

    const res = await fetch(`${baseUrl}/v1/transcribe`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      throw new Error(`GCA Transcription failed: ${res.statusText}`);
    }
    const data = (await res.json()) as { text: string };
    return { text: data.text, model: "faster-whisper-tiny" };
  },

  describeImage: async (
    input: MediaUnderstandingInput,
  ): Promise<MediaUnderstandingResult> => {
    const baseUrl = process.env.GCA_API_URL || "http://gca-service:8000";
    const formData = new FormData();
    const blob = new Blob([input.buffer], { type: input.mime });
    formData.append("file", blob, input.fileName);
    if (input.prompt) {
      formData.append("prompt", input.prompt);
    }

    const res = await fetch(`${baseUrl}/v1/describe`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      throw new Error(`GCA Description failed: ${res.statusText}`);
    }
    const data = (await res.json()) as { text: string };
    return { text: data.text, model: "qwen-vl" };
  },

  describeVideo: async (
    input: MediaUnderstandingInput,
  ): Promise<MediaUnderstandingResult> => {
    return gcaProvider.describeImage!(input);
  },
};
