"use client";
import { useState, useCallback } from "react";

const AI_ENGINE_URL = process.env.NEXT_PUBLIC_AI_ENGINE_URL || "http://localhost:8000";

export type UploadStatus = "idle" | "uploading" | "success" | "error";

export function useUpload(onSuccess?: () => void) {
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [fileName, setFileName] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const uploadPdf = useCallback(async (file: File) => {
    setStatus("uploading");
    setFileName(file.name);
    setMessage(null);

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch(`${AI_ENGINE_URL}/upload`, {
        method: "POST",
        body: form,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      setStatus("success");
      setMessage(data.message);
      onSuccess?.();
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Upload failed");
    }

    // Reset after 4s
    setTimeout(() => {
      setStatus("idle");
      setFileName(null);
      setMessage(null);
    }, 4000);
  }, []);

  return { status, fileName, message, uploadPdf };
}
