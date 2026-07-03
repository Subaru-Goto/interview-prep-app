"use client";
import { useState } from "react";

import { apiCall, apiErrorMessage } from "../lib/api";

interface CvUploadResponse {
  text: string;
  is_usable: boolean;
}

export function useCvUpload() {
  const [status, setStatus] = useState("");
  const [isUsable, setIsUsable] = useState(false);
  const [cvText, setCvText] = useState("");

  async function uploadCv(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    try {
      const data = await apiCall<CvUploadResponse>("/upload-cv", {
        method: "POST",
        body: formData,
      });
      setStatus(
        data.is_usable
          ? "✓ CV uploaded successfully"
          : "✗ Couldn't read text from this PDF — please upload a text-based PDF.",
      );
      setIsUsable(data.is_usable);
      setCvText(data.text ?? "");
    } catch (error) {
      setStatus(apiErrorMessage(error, "Something went wrong uploading your CV."));
    }
  }

  return { status, isUsable, cvText, uploadCv };
}
