import Navbar from "@/app/components/navbar";
import Image from 'next/image'
import ExerciseVideo from "@/app/components/exercise-video";
import FormChecker_Button from "@/app/components/formChecker_button";

export default function BentPage() {
    return (
        <main className="min-h-dvh overflow-x-hidden bg-blue-950">
            <div className="mx-auto flex w-full max-w-7xl flex-col items-center px-6 pt-8 sm:px-10 lg:flex-row lg:px-10" >
                <Navbar />
            </div>
            <div className="mx-auto flex w-full max-w-7xl flex-col items-center justify-between gap-5 px-6 py-8 sm:px-10 lg:flex-row lg:items-start lg:px-10" >
                <Instructions />
                <div className="flex w-full lg:py-20 flex-col items-center gap-4 lg:w-auto lg:items-center">
                    <FormChecker_Button path="/exercises/bent-over-barbell-row/form_checker" />
                    <ExerciseVideo src="/bent_ref.mp4" />
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
                            The Bent-over Barbell Row
                        </p>
                        <h2 className="mt-1 text-xl font-bold text-white sm:text-2xl lg:text-3xl">
                            Instructions
                        </h2>
                    </div>
                    <Image
                        src="/bent_affected_muscleGroups.svg"
                        width={200}
                        height={200}
                        className="h-20 w-20 shrink-0 sm:h-24 sm:w-24 lg:h-50 lg:w-50 transition-all duration-200 ease-out hover:-translate-y-1"
                        alt="Bent-over Barbell Row_Affected_Muscle_Groups"
                    />
                </div>
            </div>
            <ul className="mt-5 space-y-3 text-sm leading-7 text-slate-100 sm:text-base lg:text-lg">
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">1</span>
                    <span>Stand with your feet shoulder-width apart.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">2</span>
                    <span>Grab the bar at shoulder-width.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">3</span>
                    <span>Bend your torso until your upper-body is close to parallel to the ground, keeping your back straight and core braced.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">4</span>
                    <span>Make sure to start with your elbows close to your body and your arms fully extended.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">5</span>
                    <span>Make sure to pull the bar towards your lower chest, keeping your elbows close to your body.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">6</span>
                    <span>During the movement, make sure to keep your back straight and core braced and avoid swinging.</span>
                </li>
            </ul>
        </section>
    )
}