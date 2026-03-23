import Navbar from "@/app/components/navbar"
import ExerciseVideo from "@/app/components/exercise-video"
import Image from 'next/image'
import FormChecker_Button from "@/app/components/formChecker_button"

export default function SquatPage() {
    return (
        <main className="min-h-dvh overflow-x-hidden bg-blue-950">
            <div className="mx-auto flex w-full max-w-7xl flex-col items-center px-6 pt-8 sm:px-10 lg:flex-row lg:px-10" >
                <Navbar />
            </div>
            <div className="mx-auto flex w-full max-w-7xl flex-col items-center justify-between gap-5 px-6 py-8 sm:px-10 lg:flex-row lg:items-start lg:px-10" >
                <Instructions />
                <div className="flex w-full lg:py-20 flex-col items-center gap-4 lg:w-auto lg:items-center">
                    <FormChecker_Button path="/exercises/squat/form_checker" />
                    <ExerciseVideo src="/squat_ref.mp4" />
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
                            The Squat
                        </p>
                        <h2 className="mt-1 text-xl font-bold text-white sm:text-2xl lg:text-3xl">
                            Instructions
                        </h2>
                    </div>
                    <Image
                        src="/squat_affected_muscleGroups.svg"
                        width={200}
                        height={200}
                        className="h-20 w-20 shrink-0 sm:h-24 sm:w-24 lg:h-50 lg:w-50 transition-all duration-200 ease-out"
                        alt="Squat_Affected_Muscle_Groups"
                    />
                </div>
            </div>
            <ul className="mt-5 space-y-3 text-sm leading-7 text-slate-100 sm:text-base lg:text-lg">
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">1</span>
                    <span>Stand with your feet shoulder-width apart and your toes slightly pointed outward.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">2</span>
                    <span>Place the bar on your upper back, just below your neck.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">3</span>
                    <span>Brace your core and keep your chest up by looking ahead as you lower by bending at the hips and knees.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">4</span>
                    <span>Keep your knees from tracking too far over your toes and collapsing inward.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">5</span>
                    <span>Maintain a neutral back throughout the movement without excessive rounding or arching.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">6</span>
                    <span>Lower until your thighs reach at least parallel to the ground, or slightly below if control allows.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">7</span>
                    <span>Drive through your heels to stand back up and fully extend your hips and knees.</span>
                </li>
                <li className="flex items-start gap-3 rounded-xl border border-blue-800/60 bg-blue-900/40 px-4 py-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/90 text-xs font-bold text-blue-950">8</span>
                    <span>Repeat the movement while keeping the same posture and control on every rep.</span>
                </li>
            </ul>
        </section>
    )
}