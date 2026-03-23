import Navbar from "@/app/components/navbar"
import WebcamFeed from "@/app/components/webcam-feed"

export default function FormCheckerPage() {
    return (
        <main className="min-h-dvh overflow-hidden bg-blue-950">
            <div className="mx-auto flex w-full max-w-7xl flex-col items-center px-6 pt-8 sm:px-10 lg:flex-row lg:px-10" >
                <Navbar />
            </div>
             <div className="mx-auto flex w-full max-w-7xl flex-col items-center justify-between gap-5 px-6 py-8 sm:px-10 lg:flex-row lg:items-start lg:px-10" >
                <Title />
            </div>
            <div className="mx-auto flex w-full max-w-7xl px-6 pb-8 sm:px-10 lg:px-10">
                <WebcamFeed exercise="squat" />
            </div>
        </main >
    )
}


function Title() {
    return (
        <section className="w-full max-w-5xl text-left">
            <div className="rounded-2xl border border-blue-800/60 bg-blue-900/30 px-4 py-4 sm:px-5">
                <div className="flex flex-row items-start justify-between gap-4 sm:items-center">
                    <div className="flex flex-col items-start gap-1">
                        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300 sm:text-sm">
                            The Squat
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