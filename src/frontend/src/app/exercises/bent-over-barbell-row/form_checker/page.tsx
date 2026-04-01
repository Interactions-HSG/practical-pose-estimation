import Navbar from "@/app/components/navbar"
import WebcamFeed from "@/app/components/webcam-feed"

export default function FormCheckerPage() {
    return (
        <main className="min-h-dvh overflow-hidden bg-blue-950">
            <div className="mx-auto flex w-full max-w-7xl flex-col items-center px-6 pt-8 sm:px-10 lg:flex-row lg:px-10" >
                <Navbar />
            </div>
             <div className="mx-auto flex w-full max-w-7xl flex-col items-center gap-5 px-6 py-8 sm:px-10 lg:flex-row lg:items-start lg:px-10" >
                <Title />
            </div>
            <div className="mx-auto flex w-full max-w-7xl flex-col items-center justify-between gap-5 px-6 py-0 sm:px-10 lg:flex-row lg:items-start lg:px-10">
                <ImportantNotice />
            </div>
            <div className="mx-auto flex w-full max-w-7xl px-6 pb-8 sm:px-10 lg:px-10">
                <WebcamFeed exercise="bent" />
            </div>
        </main >
    )
}


function Title() {
    return (
        <section className="flex w-full max-w-5xl text-left">
            <div className="w-full rounded-2xl border border-blue-800/60 bg-blue-900/30 px-4 py-4 sm:px-5">
                <div className="flex flex-row items-start justify-between gap-4 sm:items-center">
                    <div className="flex flex-col items-start gap-1">
                        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300 sm:text-sm">
                            The Bent-over Barbell Row
                        </p>
                        <h2 className="mt-1 text-xl font-bold text-white sm:text-2xl lg:text-3xl">
                            Form Checker
                        </h2>
                    </div>
                </div>
            </div>
        </section>
    )
}

function ImportantNotice() {
    return (
        <section className="w-full max-w-5xl">
            <div className="rounded-2xl border border-yellow-600/60 bg-yellow-200 px-4 py-4 sm:px-5 flex items-center w-full">
                <span className="mr-4 text-3xl">⚠️</span>
                <div className="flex-1">
                    <h3 className="text-lg font-bold text-yellow-900 mb-1">Important Notice</h3>
                    <p className="text-yellow-900 text-base leading-relaxed">
                        The Form Checker uses Artificial Intelligence to detect your form in real-time and provide personalized feedback.<br className="hidden sm:block" />
                        <span className="font-semibold">Inaccuracies may occur</span> due to lighting or camera angle, and the AI may occasionally provide incorrect feedback.<br className="hidden sm:block" />
                        <span className="font-semibold">Always prioritize safety</span> and listen to your body. If you feel pain or discomfort, stop exercising and consult a professional.
                    </p>
                </div>
            </div>
        </section>
    )
}