import Navbar from "@/app/components/navbar"
import ExerciseVideo from "@/app/components/exercise-video"
import Image from 'next/image'
import FormChecker_Button from "@/app/components/formChecker_button"

export default function BenchPage() {
    return (
        <main className="min-h-dvh overflow-x-hidden bg-blue-950">
            <div className="mx-auto flex w-full max-w-7xl flex-col items-center px-6 pt-8 sm:px-10 lg:flex-row lg:px-10" >
                <Navbar />
            </div>
            <div className="mx-auto flex w-full max-w-7xl flex-col items-center justify-between gap-5 px-6 py-8 sm:px-10 lg:flex-row lg:items-start lg:px-10" >
                <Instructions />
                <div className="flex w-full lg:py-20 flex-col items-center gap-4 lg:w-auto lg:items-center">
                    <FormChecker_Button path="/exercises/bench-press/form_checker" />
                    <ExerciseVideo src="/bench_ref.mp4" />
                </div>
            </div>
        </main >
    )
}

function Instructions() {
    return (
        <section className="w-full max-w-3xl text-left">
            <div className="rounded-2xl border border-blue-800/60 bg-blue-900/30 px-4 py-4 sm:px-5">
                <div className="flex flex-row items-start justify-between gap-4 sm:items-center">
                    <div className="flex flex-col items-start gap-1">
                        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300 sm:text-sm">
                            The Bench Press
                        </p>
                        <h2 className="mt-1 text-xl font-bold text-white sm:text-2xl lg:text-3xl">
                            Instructions
                        </h2>
                    </div>
                    <Image
                        src="/bench_affected_muscleGroups.svg"
                        width={200}
                        height={200}
                        className="h-20 w-20 shrink-0 sm:h-24 sm:w-24 lg:h-50 lg:w-50 transition-all duration-200 ease-out hover:-translate-y-1"
                        alt="Bench Press_Affected_Muscle_Groups"
                    />
                </div>
            </div>
            <ul className="mt-5 space-y-3 text-sm leading-7 text-slate-100 sm:text-base lg:text-lg">
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">1</span>
                    <span>Lie flat on the bench with your feet flat on the ground.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">2</span>
                    <span>Set your shoulder blades by pulling them back and down (scapular retraction), and keep a slight natural arch in your lower back.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">3</span>
                    <span>Grab the bar with a grip slightly wider than shoulder-width, and stack your wrists over your elbows to avoid bent wrists.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">4</span>
                    <span>Lower the bar in a slightly diagonal path to your lower chest, then press it back up over your shoulder line.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">5</span>
                    <span>When pushing back up, make sure that your arms are fully extended at the top of the movement.</span>
                </li>
            </ul>
        </section>
    )
}