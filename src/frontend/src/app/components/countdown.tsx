import { useEffect, useState } from "react";

const COUNTDOWN_AMOUNT_TOTAL = 8;

type CountdownProps = {
    startDelayMs?: number;
};

export default function Countdown({ startDelayMs = 0 }: CountdownProps) {
    const [seconds, setSeconds] = useState<number>(COUNTDOWN_AMOUNT_TOTAL);
    const [started, setStarted] = useState<boolean>(startDelayMs === 0);

    useEffect(() => {
        if (startDelayMs === 0) {
            setStarted(true);
            return;
        }

        const startTimeout = window.setTimeout(() => {
            setStarted(true);
        }, startDelayMs);

        return () => {
            window.clearTimeout(startTimeout);
        };
    }, [startDelayMs]);

    useEffect(() => {
        if (!started || seconds <= 0) {
            return;
        }

        const timeout = window.setTimeout(() => {
            setSeconds((state) => state - 1);
        }, 1000);

        return () => {
            window.clearTimeout(timeout);
        };
    }, [seconds, started]);

    return <span className="text-8xl">{seconds}</span>;
}