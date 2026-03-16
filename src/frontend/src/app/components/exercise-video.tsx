"use client";

import { useEffect, useRef } from "react";

type ExerciseVideoProps = {
  src: string;
};

export default function ExerciseVideo({ src }: ExerciseVideoProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    const videoElement = videoRef.current;

    if (!videoElement) {
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          void videoElement.play().catch(() => {
            // Ignore autoplay rejections from the browser.
          });
          return;
        }

        videoElement.pause();
      },
      {
        threshold: 0.6,
      },
    );

    observer.observe(videoElement);

    return () => {
      observer.disconnect();
      videoElement.pause();
    };
  }, []);

  return (
    <video
      ref={videoRef}
      muted
      loop
      playsInline
      preload="metadata"
      className="h-auto w-full max-w-72 rounded-lg sm:max-w-96 lg:max-w-105"
    >
      <source src={src} type="video/mp4" />
    </video>
  );
}