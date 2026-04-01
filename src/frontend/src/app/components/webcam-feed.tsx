"use client";

import { useEffect, useRef, useState } from "react";
import Countdown from "./countdown";
import ExerciseVideo from "./exercise-video";


type WebcamFeedProps = {
    exercise: "squat" | "bench" | "bent";
};

export default function WebcamFeed({ exercise }: WebcamFeedProps) {
    // Streaming configuration
    const STREAM_CONFIG = {
        TARGET_FPS: 12,
        STREAM_MAX_WIDTH: 360,
        JPEG_QUALITY: 0.38,
        ADAPTIVE_MODE: true,
        MIN_WIDTH: 256,
        MIN_QUALITY: 0.28,
    } as const;

    const STREAM_INTERVAL_MS = Math.max(40, Math.round(1000 / STREAM_CONFIG.TARGET_FPS));

    // Refs for video, canvas, WebSocket, media stream, and various flags and timers
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const recordedBlobsRef = useRef<Blob[]>([]);
    const sendingRef = useRef<boolean>(false);
    const inFlightTimeoutRef = useRef<number | null>(null);
    const lastSendAtRef = useRef<number>(0);
    const adaptiveWidthRef = useRef<number>(STREAM_CONFIG.STREAM_MAX_WIDTH);
    const adaptiveQualityRef = useRef<number>(STREAM_CONFIG.JPEG_QUALITY);
    const lastAdaptAtRef = useRef<number>(0);
    const receiveTimesRef = useRef<number[]>([]);
    const overlayTimeoutRef = useRef<number | null>(null);
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const audioQueueRef = useRef<string[]>([]);
    const audioPlayingRef = useRef<boolean>(false);
    const audioUnlockedRef = useRef<boolean>(false);
    const currentSetRef = useRef<number>(1);
    const recordedVideoUrlRef = useRef<string>("");

    // State for UI status and performance metrics
    const [status, setStatus] = useState<string>("Initializing camera...");
    const [connected, setConnected] = useState<boolean>(false);
    const [annotatedSrc, setAnnotatedSrc] = useState<string>("");
    const [isRunning, setIsRunning] = useState<boolean>(false);
    const [perf, setPerf] = useState<string>("");
    const [showPlacementOverlay, setShowPlacementOverlay] = useState<boolean>(false);
    const [personDetected, setPersonDetected] = useState<boolean>(false);
    const [initialDetectionTimerDone, setInitialDetectionTimerDone] = useState<boolean>(false);
    const [targetReps, setTargetReps] = useState<number>(10);
    const [currentReps, setCurrentReps] = useState<number>(0);
    const [currentSet, setCurrentSet] = useState<number>(1);
    const [totalSets] = useState<number>(3);
    const [showFeedbackScreen, setShowFeedbackScreen] = useState<boolean>(false);
    const [showExerciseVideo, setShowExerciseVideo] = useState<boolean>(false);
    const [targetRepsInput, setTargetRepsInput] = useState<string>("10");
    const [uploadStatus, setUploadStatus] = useState<string>("");
    const [recordedVideoUrl, setRecordedVideoUrl] = useState<string>("");
    const [sessionId, setSessionId] = useState<string>("");
    const [aiFeedback, setAIFeedback] = useState<string>("");

    const normalizeAudioUrl = (rawUrl: string) => {
        try {
            const normalized = new URL(rawUrl, window.location.origin);

            // Avoid mixed-content blocking when frontend is served over HTTPS.
            if (window.location.protocol === "https:" && normalized.protocol === "http:") {
                normalized.protocol = "https:";
            }

            return normalized.toString();
        } catch {
            return rawUrl;
        }
    };

    const showCountdownOverlay =
        isRunning && !showPlacementOverlay && personDetected && !initialDetectionTimerDone;

    const playNextAudio = () => {
        const audio = audioRef.current;
        if (!audio || audioPlayingRef.current) return;

        const nextUrl = audioQueueRef.current.shift();
        if (!nextUrl) return;

        audioPlayingRef.current = true;
        audio.src = normalizeAudioUrl(nextUrl);
        audio.currentTime = 0;

        void audio.play()
    };

    const enqueueAudio = (url: string) => {
        if (!url) return;
        audioQueueRef.current.push(url);
        playNextAudio();
    };

    const AudioPlayback = async () => {

        const audio = audioRef.current ?? new Audio();
        audio.preload = "auto";
        audio.crossOrigin = "anonymous";

        //Check if audio playback is already unlocked (e.g. from previous session)
        audio.onended = () => {
            audioPlayingRef.current = false;
            playNextAudio();
        };

        audio.onerror = () => {
            audioPlayingRef.current = false;
            playNextAudio();
        };

        audioRef.current = audio;
    };

    const getCameraGuideImage = () => {
        if (exercise === "bench") {
            return currentSet === 1 ? "/cam_bench_front.svg" :
                currentSet === 2 ? "/cam_bench_side.svg" :
                    "/cam_bench_otherSide.svg";
        }
        return currentSet === 1 ? "/cam_front.svg" :
            currentSet === 2 ? "/cam_side.svg" :
                "/cam_otherSide.svg";
    };

    useEffect(() => { currentSetRef.current = currentSet; }, [currentSet]);
    useEffect(() => { recordedVideoUrlRef.current = recordedVideoUrl; }, [recordedVideoUrl]);

    // Main effect to handle camera access, WebSocket connection, and streaming logic
    useEffect(() => {
        if (!isRunning) {
            return;
        }

        let intervalId: number | null = null;

        const start = async () => {
            try {
                // Request camera access and start video stream
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        width: { ideal: 960 },
                        height: { ideal: 540 },
                        facingMode: "user",
                    },
                    audio: false,
                });
                streamRef.current = stream;

                let mimeType = "";
                let ext = "webm";
                if (MediaRecorder.isTypeSupported("video/mp4;codecs=avc1.42E01E,mp4a.40.2")) {
                    mimeType = "video/mp4;codecs=avc1.42E01E,mp4a.40.2";
                    ext = "mp4";
                } else if (MediaRecorder.isTypeSupported("video/webm;codecs=vp9")) {
                    mimeType = "video/webm;codecs=vp9";
                    ext = "webm";
                } else if (MediaRecorder.isTypeSupported("video/webm")) {
                    mimeType = "video/webm";
                    ext = "webm";
                }
                mediaRecorderRef.current = new MediaRecorder(stream, ...(mimeType ? [{ mimeType }] : []));
                // Setup MediaRecorder event handlers
                recordedBlobsRef.current = [];
                mediaRecorderRef.current.ondataavailable = (event: BlobEvent) => {
                    if (event.data && event.data.size > 0) {
                        recordedBlobsRef.current.push(event.data);
                    }
                };
                mediaRecorderRef.current.onstop = async () => {
                    const usedMime = mediaRecorderRef.current?.mimeType || mimeType || "video/webm";
                    const superBlob = new Blob(recordedBlobsRef.current, { type: usedMime });
                    let realExt = ext;
                    if (usedMime.includes("mp4")) realExt = "mp4";
                    else if (usedMime.includes("webm")) realExt = "webm";
                    const prevUrl = recordedVideoUrlRef.current;
                    if (prevUrl) {
                        URL.revokeObjectURL(prevUrl);
                    }
                    const newUrl = URL.createObjectURL(superBlob);
                    setRecordedVideoUrl(newUrl);
                    recordedVideoUrlRef.current = newUrl;
                    setUploadStatus("Uploading video...");
                    try {
                        const formData = new FormData();
                        formData.append("file", superBlob, `${exercise}_${currentSetRef.current}_feedback.${realExt}`);
                        formData.append("exercise", exercise);
                        formData.append("session_id", sessionId);
                        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_WS_URL;
                        console.log("Blob size (MB):", (superBlob.size));
                        const res = await fetch(`${backendUrl}/upload`, {
                            method: "POST",
                            body: formData,
                        });
                        if (res.ok) {
                            setUploadStatus("Upload successful!");
                        } else {
                            setUploadStatus("Upload failed.");
                        }
                    } catch (err) {
                        setUploadStatus("Upload failed.");
                    }
                    setTimeout(() => setUploadStatus(""), 4000);
                };

                recordedBlobsRef.current = [];


                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    await videoRef.current.play();
                }

                setStatus("Connecting to backend...");

                const envBackendBase = process.env.NEXT_PUBLIC_BACKEND_WS_URL?.trim();
                let wsUrl: string;

                if (envBackendBase) {
                    const normalizedBase = envBackendBase.replace(/^https:\/\//i, "wss://")
                    wsUrl = `${normalizedBase}/livestream?exercise=${exercise}`;
                } else {
                    const wsHost = window.location.hostname;
                    const wsPort = process.env.NEXT_PUBLIC_BACKEND_PORT ?? "8000";
                    wsUrl = `wss://${wsHost}:${wsPort}/livestream?exercise=${exercise}`;
                }

                const ws = new WebSocket(wsUrl);
                ws.binaryType = "arraybuffer";
                wsRef.current = ws;

                ws.onopen = () => {

                    // Handling of websocket connection open: update status, initialize adaptive streaming parameters, and start sending frames at regular intervals
                    setConnected(true);
                    setStatus("Connected. Running live form check...");
                    adaptiveWidthRef.current = STREAM_CONFIG.STREAM_MAX_WIDTH;
                    adaptiveQualityRef.current = STREAM_CONFIG.JPEG_QUALITY;
                    lastAdaptAtRef.current = 0;

                    intervalId = window.setInterval(() => {

                        // Don't send a new frame if the previous one is still being processed or if WebSocket isn't ready
                        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
                        if (!videoRef.current || !canvasRef.current) return;
                        if (sendingRef.current) return;

                        // Draw current video frame to canvas and send as JPEG blob but only if video metadata is loaded 
                        const video = videoRef.current;
                        const canvas = canvasRef.current;
                        if (video.videoWidth === 0 || video.videoHeight === 0) return;

                        // Keep payload small for tunnel/mobile links to reduce latency.
                        const scaledWidth = Math.min(video.videoWidth, adaptiveWidthRef.current);
                        const scaledHeight = Math.round((scaledWidth / video.videoWidth) * video.videoHeight);

                        canvas.width = scaledWidth;
                        canvas.height = scaledHeight;
                        const ctx = canvas.getContext("2d");
                        if (!ctx) return;

                        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                        sendingRef.current = true;

                        // Convert canvas to JPEG blob and send via WebSocket
                        canvas.toBlob((blob) => {
                            if (!blob || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
                                sendingRef.current = false;
                                return;
                            }
                            lastSendAtRef.current = performance.now();
                            wsRef.current.send(blob);

                            // If response is lost, unlock sending so stream does not freeze on one frame.
                            if (inFlightTimeoutRef.current !== null) {
                                window.clearTimeout(inFlightTimeoutRef.current);
                            }
                            inFlightTimeoutRef.current = window.setTimeout(() => {
                                sendingRef.current = false;
                                setStatus("High latency detected, retrying...");
                            }, 5000);
                        }, "image/jpeg", adaptiveQualityRef.current);
                    }, STREAM_INTERVAL_MS);


                };

                ws.onmessage = (event) => {
                    // Handle incoming messages: control messages as JSON strings and annotated frames as binary data
                    if (typeof event.data === "string") {
                        try {
                            const payload = JSON.parse(event.data) as {
                                type?: string;
                                url?: string;
                                detected?: boolean;
                                timer_done?: boolean;
                                rep_counter?: number;
                                session_id?: string;
                            };

                            if (payload.type === "audio_feedback" && payload.url) {
                                enqueueAudio(payload.url);
                            }

                            else if (payload.type === "detection_status") {
                                setPersonDetected(payload.detected === true);
                                setInitialDetectionTimerDone(payload.timer_done === true);
                            }
                            else if (payload.type === "rep_update") {
                                setCurrentReps(payload.rep_counter ?? currentReps);
                            }
                            else if (payload.type === "session_id") {
                                setSessionId(payload.session_id ?? "")
                            }

                        } catch {
                            // Ignore malformed control messages and continue receiving frames.
                        }
                        return;
                    }

                    //Receive annotated frame as ArrayBuffer, convert to Blob and create object URL for display
                    const arrayBuffer = event.data as ArrayBuffer;
                    const blob = new Blob([arrayBuffer], { type: "image/jpeg" });
                    const objectUrl = URL.createObjectURL(blob);

                    setAnnotatedSrc((prev) => {
                        if (prev) URL.revokeObjectURL(prev);
                        return objectUrl;
                    });

                    const now = performance.now();
                    const rttMs = now - lastSendAtRef.current;
                    const recent = receiveTimesRef.current.filter((t) => now - t < 3000);
                    recent.push(now);
                    receiveTimesRef.current = recent;
                    const measuredFps = recent.length / 3;

                    // Auto-adjust stream settings to keep it smooth on unstable tunnel/mobile links.
                    if (STREAM_CONFIG.ADAPTIVE_MODE && now - lastAdaptAtRef.current > 1200) {
                        const tooSlow = rttMs > 450 || measuredFps < STREAM_CONFIG.TARGET_FPS * 0.55;
                        const healthy = rttMs < 180 && measuredFps > STREAM_CONFIG.TARGET_FPS * 0.9;

                        if (tooSlow) {
                            adaptiveWidthRef.current = Math.max(STREAM_CONFIG.MIN_WIDTH, Math.round(adaptiveWidthRef.current * 0.85));
                            adaptiveQualityRef.current = Math.max(STREAM_CONFIG.MIN_QUALITY, Number((adaptiveQualityRef.current - 0.05).toFixed(2)));
                            setStatus("Adapting stream for lower latency...");
                            lastAdaptAtRef.current = now;
                        } else if (healthy) {
                            adaptiveWidthRef.current = Math.min(STREAM_CONFIG.STREAM_MAX_WIDTH, Math.round(adaptiveWidthRef.current * 1.08));
                            adaptiveQualityRef.current = Math.min(STREAM_CONFIG.JPEG_QUALITY, Number((adaptiveQualityRef.current + 0.03).toFixed(2)));
                            lastAdaptAtRef.current = now;
                        }
                    }

                    setPerf(
                        `${measuredFps.toFixed(1)} fps | ${Math.round(rttMs)} ms RTT | ${adaptiveWidthRef.current}px q${adaptiveQualityRef.current.toFixed(2)}`
                    );

                    // Allow next frame to be sent after receiving response
                    if (inFlightTimeoutRef.current !== null) {
                        window.clearTimeout(inFlightTimeoutRef.current);
                        inFlightTimeoutRef.current = null;
                    }
                    sendingRef.current = false;
                };

                ws.onerror = () => {
                    setStatus("WebSocket error. Is backend running on port 8000?");
                    setConnected(false);
                    setIsRunning(false);
                    setPersonDetected(false);
                    setInitialDetectionTimerDone(false);
                    sendingRef.current = false;
                };

                ws.onclose = () => {
                    setStatus("Connection closed.");
                    setConnected(false);
                    setIsRunning(false);
                    setPersonDetected(false);
                    setInitialDetectionTimerDone(false);
                    sendingRef.current = false;
                };
            } catch {
                setStatus("Camera access denied or unavailable.");
            }
        };

        start();

        return () => {
            // Cleanup on unmount: stop video stream, close WebSocket, revoke object URLs, and clear intervals
            if (intervalId !== null) window.clearInterval(intervalId);
            if (inFlightTimeoutRef.current !== null) {
                window.clearTimeout(inFlightTimeoutRef.current);
                inFlightTimeoutRef.current = null;
            }
            if (overlayTimeoutRef.current !== null) {
                window.clearTimeout(overlayTimeoutRef.current);
                overlayTimeoutRef.current = null;
            }
            if (wsRef.current) wsRef.current.close();
            wsRef.current = null;
            if (streamRef.current) {
                streamRef.current.getTracks().forEach((track) => track.stop());
                streamRef.current = null;
            }
            if (videoRef.current) {
                videoRef.current.srcObject = null;
            }
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current.onended = null;
                audioRef.current.onerror = null;
                audioRef.current = null;
            }
            if (audioContextRef.current) {
                void audioContextRef.current.close();
                audioContextRef.current = null;
            }
            audioQueueRef.current = [];
            audioPlayingRef.current = false;
            audioUnlockedRef.current = false;
            setConnected(false);
            sendingRef.current = false;
            receiveTimesRef.current = [];
            adaptiveWidthRef.current = STREAM_CONFIG.STREAM_MAX_WIDTH;
            adaptiveQualityRef.current = STREAM_CONFIG.JPEG_QUALITY;
            setPerf("");
            setAnnotatedSrc((prev) => {
                if (prev) URL.revokeObjectURL(prev);
                return "";
            });
        };
    }, [
        exercise,
        isRunning,
        STREAM_INTERVAL_MS,
    ]);

    // Start recording only after the initial detection countdown has completed.
    useEffect(() => {
        if (!isRunning || !initialDetectionTimerDone) return;

        const recorder = mediaRecorderRef.current;
        if (!recorder) return;
        if (recorder.state === "inactive") {
            recordedBlobsRef.current = [];
            recorder.start(1000);
        }
    }, [isRunning, initialDetectionTimerDone]);

    // Auto-complete set when target reps reached
    useEffect(() => {
        if (isRunning && currentReps > 0 && currentReps >= targetReps) {
            handleEndSet();
        }
    }, [currentReps, targetReps, isRunning]);

    // Handlers for starting exercise, ending set, moving to next set, and stopping exercise
    const handleStart = async () => {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_WS_URL;
        for (let setNum = 1; setNum <= totalSets; setNum++) {
            const videoPath = `/${exercise}_${setNum}_feedback.mp4`;
            try {

                // Delete any existing feedback videos and snapshots from previous sessions to avoid confusion and free up storage
                await fetch(`${backendUrl}/delete_video`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ path: videoPath })
                });

                await fetch(`${backendUrl}/delete_snapshot`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" }
                });

            } catch (e) {
                console.error(`Error occurred while deleting video: ${videoPath}`, e);
            }
        }
        recordedBlobsRef.current = [];
        const prevUrl = recordedVideoUrlRef.current;
        if (prevUrl) {
            URL.revokeObjectURL(prevUrl);
            setRecordedVideoUrl("");
            recordedVideoUrlRef.current = "";
        }
        AudioPlayback();
        setStatus("Initializing camera...");
        setShowPlacementOverlay(true);
        if (overlayTimeoutRef.current !== null) {
            window.clearTimeout(overlayTimeoutRef.current);
        }
        overlayTimeoutRef.current = window.setTimeout(() => {
            setShowPlacementOverlay(false);
            overlayTimeoutRef.current = null;
        }, 5000);
        setShowFeedbackScreen(false);
        setCurrentReps(0);
        setIsRunning(true);
    };

    // Handle end of set: stop recording, show feedback screen, poll for feedback video availability, and fetch AI feedback from backend. Also close WebSocket connection to stop live stream and free up resources while user reviews feedback.
    const handleEndSet = async () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
            mediaRecorderRef.current.stop();
        }

        setIsRunning(false)
        setShowFeedbackScreen(true);
        setShowExerciseVideo(false);

        const videoPath = `/${exercise}_${currentSet}_feedback.mp4`;
        let pollInterval: NodeJS.Timeout | null = null;
        const checkVideo = async () => {
            try {
                const res = await fetch(videoPath, { method: "HEAD" });
                if (res.ok) {
                    setShowExerciseVideo(true);
                    if (pollInterval) clearInterval(pollInterval);
                }
            } catch (e) {
                // ignore
            }
        };
        pollInterval = setInterval(checkVideo, 3000);
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_WS_URL;
        const res = await fetch(`${backendUrl}/generate_feedback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sessionId, exercise }),
        });
        const data = await res.json();
        setAIFeedback(data.feedback);

        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    };

    const handleNextSet = () => {
        if (currentSet < totalSets) {
            // Send reset command via WebSocket if possible
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: "reset_reps", exercise }));
            }
            setCurrentSet(currentSet + 1);
            setCurrentReps(0);
            setShowFeedbackScreen(false);
            handleStart();
        }
    };

    const handleStop = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
            mediaRecorderRef.current.stop();
        }
        setStatus("Stopped.");
        setShowPlacementOverlay(false);
        setPersonDetected(false);
        setInitialDetectionTimerDone(false);
        setCurrentReps(0);
        setCurrentSet(1);
        setShowFeedbackScreen(false);
        setTargetRepsInput(String(targetReps));
        if (overlayTimeoutRef.current !== null) {
            window.clearTimeout(overlayTimeoutRef.current);
            overlayTimeoutRef.current = null;
        }
        setIsRunning(false);
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    };


    //Frontend UI with connection status and annotated video feed (or placeholder while waiting for first frame)
    return (
        <section className="flex w-full max-w-5xl">
            <div className="flex flex-col w-full items-center rounded-2xl border border-blue-800/60 bg-blue-900/30 p-4 sm:p-5">
                <ConnectionStatus />

                <div className="mb-4 w-full rounded-lg border border-blue-800/60 bg-blue-900/20 p-4">
                    <label className="block text-sm font-semibold text-slate-300 mb-2 text-center">
                        How many Repetitions are you planning to do?
                    </label>
                    <div className="flex gap-2 justify-center max-w-xs mx-auto">
                        <input
                            type="text"
                            inputMode="numeric"
                            value={targetRepsInput}
                            onChange={(e) => {
                                const val = e.target.value.replace(/[^0-9]/g, "");
                                setTargetRepsInput(val);
                            }}
                            onBlur={() => {
                                const num = parseInt(targetRepsInput) || 10;
                                const validated = Math.max(1, Math.min(50, num));
                                setTargetReps(validated);
                                setTargetRepsInput(String(validated));
                            }}
                            disabled={isRunning}
                            className="flex-1 rounded-lg bg-slate-700/50 px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        />
                        <button
                            type="button"
                            onClick={() => {
                                setTargetReps(10);
                                setTargetRepsInput("10");
                            }}
                            disabled={isRunning}
                            className="rounded-lg bg-slate-700/50 px-3 py-2 text-white hover:bg-slate-600/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            Reset
                        </button>
                    </div>
                </div>

                <RepSetCounter />

                {/* Connection status, rep/set counters, and performance metrics */}
                <p className="mb-4 text-sm text-slate-300">{status}</p>
                {perf && <p className="mb-4 text-xs text-slate-400">{perf}</p>}


                <div className="mb-4 flex items-center gap-3">
                    {!isRunning && !showFeedbackScreen ? (
                        <button
                            type="button"
                            onClick={() => {
                                void handleStart();
                            }}
                            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-red-500"
                        >
                            Start Exercise
                        </button>
                    ) : isRunning ? (
                        <>
                            <button
                                type="button"
                                onClick={handleStop}
                                className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-slate-600"
                            >
                                Stop Exercise
                            </button>
                            <button
                                type="button"
                                onClick={handleEndSet}
                                className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-slate-600"
                            >
                                End Set
                            </button>
                        </>
                    ) : null}
                </div>


                {/* Full-window Feedback Screen Overlay */}
                {showFeedbackScreen && (
                    <div className="fixed inset-0 z-50 overflow-y-auto bg-blue-950/95 p-4">
                        <div className="mx-auto flex w-full max-w-4xl flex-col gap-5 rounded-2xl border border-blue-800/60 bg-blue-900/30 p-4 text-center sm:p-6">
                            <div className="flex flex-col items-center gap-2">
                                <h2 className="text-4xl font-bold text-white">Set {currentSet} Complete! 🎉</h2>
                                <p className="text-2xl text-slate-300">
                                    You completed <span className="text-green-400 font-bold text-3xl">{currentReps}/{targetReps}</span> reps
                                </p>
                            </div>

                            <div className="rounded-xl border border-blue-800/60 bg-blue-950/40 p-3 sm:p-4">
                                <h3 className="mb-3 text-lg font-semibold text-white">Set Video</h3>
                                {showExerciseVideo ? (
                                    <ExerciseVideo src={`/${exercise}_${currentSet}_feedback.mp4`} />
                                ) : (
                                    <div className="flex h-40 items-center justify-center px-4 text-center text-sm text-slate-400">
                                        {"Video loading..."}
                                    </div>
                                )}
                            </div>

                            <div className="rounded-xl border border-blue-800/60 bg-blue-950/40 p-4 text-left">
                                <h3 className="mb-3 text-center text-2xl font-bold text-white">AI Feedback</h3>
                                {aiFeedback ? (
                                    <p className="whitespace-pre-line text-base leading-relaxed text-slate-200 sm:text-lg">
                                        {aiFeedback}
                                    </p>
                                ) : (
                                    <p className="text-center text-sm text-slate-400">
                                        {"Generating AI feedback..."}
                                    </p>
                                )}
                            </div>

                            <div className="flex flex-col gap-3 pt-1">
                                {currentSet < totalSets ? (
                                    <>
                                        <button
                                            type="button"
                                            onClick={handleNextSet}
                                            className="rounded-lg bg-green-600 px-6 py-3 text-lg font-semibold text-white transition-colors hover:bg-green-500"
                                        >
                                            Next Set
                                        </button>
                                        <button
                                            type="button"
                                            onClick={handleStop}
                                            className="rounded-lg bg-slate-700 px-6 py-3 text-lg font-semibold text-white transition-colors hover:bg-slate-600"
                                        >
                                            Stop Exercise
                                        </button>
                                    </>
                                ) : (
                                    <button
                                        type="button"
                                        onClick={handleStop}
                                        className="rounded-lg bg-green-600 px-6 py-3 text-lg font-semibold text-white transition-colors hover:bg-green-500"
                                    >
                                        Finish Workout 🏆
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Livestream Window */}
                <div className="relative h-104 w-full overflow-hidden rounded-xl border border-blue-800/60 bg-black/30 md:h-136">
                    {uploadStatus && (
                        <div className="absolute top-2 left-2 z-30 bg-slate-800/90 text-white px-3 py-1 rounded shadow">
                            {uploadStatus}
                        </div>
                    )}
                    {showPlacementOverlay && (
                        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-black/80 p-4 text-center">
                            <img src={getCameraGuideImage()} alt="Camera placement guide" className="max-h-80 w-auto md:max-h-96" />
                        </div>
                    )}
                    {showCountdownOverlay && (
                        <div className="absolute inset-0 z-10 flex items-center justify-center">
                            <div className="rounded-full bg-green-500/70 px-4 py-2 text-sm font-semibold text-white backdrop-blur-sm">
                                <Countdown startDelayMs={1000} />
                            </div>
                        </div>
                    )}
                    {annotatedSrc ? (
                        <img src={annotatedSrc} alt="Annotated output" className="h-full w-full object-fill" />
                    ) : (
                        <div className="flex h-full items-center justify-center px-4 text-center text-sm text-slate-400">
                            {isRunning ? "Waiting for first processed frame..." : ""}
                        </div>
                    )}
                </div>
            </div>

            <video ref={videoRef} className="hidden" playsInline muted autoPlay />
            <canvas ref={canvasRef} className="hidden" />
            <audio ref={audioRef} className="hidden" preload="auto" />
        </section>
    );

    function ConnectionStatus() {
        return (
            <div className="mb-3 flex items-center justify- gap-3">
                <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${connected
                        ? "bg-green-600 text-cyan-200"
                        : "bg-blue-900/60 text-slate-300"
                        }`}
                >
                    {connected ? "Connected" : "Disconnected"}
                </span>
            </div>
        )
    }

    function RepSetCounter() {
        return (
            <div className="flex w-full flex-row items-center justify-center gap-8">
                <div className="mb-4 w-full rounded-lg border border-blue-800/60 bg-blue-900/20 p-4 text-center">
                    <p className="text-sm font-semibold text-slate-300 mb-2">Set</p>
                    <p className="text-3xl font-bold text-slate-300">
                        {currentSet} / {totalSets}
                    </p>
                </div>
                <div className="mb-4 w-full rounded-lg border border-blue-800/60 bg-blue-900/20 p-4 text-center">
                    <p className="text-sm font-semibold text-slate-300 mb-2">Reps Completed</p>
                    <p className="text-3xl font-bold text-slate-300">
                        {currentReps} / {targetReps}
                    </p>
                </div>
            </div>
        )
    }
}