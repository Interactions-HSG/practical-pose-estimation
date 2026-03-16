import Image from 'next/image'
import Link from 'next/link'

export default function Home() {
  return (
    <main className="h-dvh overflow-hidden bg-blue-950">
      <div className="mx-auto flex h-full w-full max-w-6xl flex-col items-center justify-center gap-6 px-6 py-8 sm:px-10 sm:py-10 lg:flex-row lg:items-center lg:justify-between lg:px-25 lg:pl-30 lg:py-12 xl:px-10 2xl:max-w-7xl">
        <Title />
        <Exercise_Block />
      </div>
    </main>

  );
}

function Title() {
  return (
    <div className="flex w-full flex-col items-center gap-7 text-center sm:gap-10 lg:items-start lg:text-left">
      <h1 className="text-4xl font-extrabold leading-tight text-white sm:text-5xl lg:text-6xl xl:text-7xl">
        <span className="inline-block transition-all duration-200 ease-out hover:-translate-y-1 hover:text-blue-50">
          Welcome to
        </span>{' '}
        <br />
        <span className="inline-block text-blue-200 transition-all duration-200 ease-out hover:-translate-y-1 lg:pl-6 xl:pl-8">Visual Spotter</span>
      </h1>
      <div className="flex flex-row items-center gap-8 sm:gap-12 lg:gap-16 lg:pl-6 xl:pl-8">
        <Image
          src="/dumbbell.svg"
          width={100}
          height={100}
          className="h-14 w-14 sm:h-20 sm:w-20 lg:h-24 lg:w-24 transition-all duration-200 ease-out hover:-translate-y-1"
          alt="Dumbbell Icon"
        />
        <Image
          src="/weight.svg"
          width={100}
          height={100}
          className="h-14 w-14 sm:h-20 sm:w-20 lg:h-24 lg:w-24 transition-all duration-200 ease-out hover:-translate-y-1"
          alt="Weight Icon"
        />
        <Image
          src="/bench.svg"
          width={100}
          height={100}
          className="h-14 w-14 sm:h-20 sm:w-20 lg:h-24 lg:w-24 transition-all duration-200 ease-out hover:-translate-y-1"
          alt="Bench Icon"
        />
      </div>
    </div>
  );
}

function Exercise_Block() {
  return (
    <div className="flex w-full max-w-sm flex-col items-center gap-6 px-4 py-6 sm:gap-8 sm:py-8 lg:py-0">
      <Link href="/exercises/squat"
        className="flex h-14 w-full max-w-64 items-center justify-center rounded-lg bg-blue-400 px-4 text-center text-white transition-all duration-200 ease-out will-change-transform hover:-translate-y-1 hover:bg-sky-300 hover:shadow-[0_12px_30px_rgba(96,165,250,0.35)] active:translate-y-0 active:scale-[0.98] xl:h-16 xl:max-w-72 xl:text-xl">
        Squat
      </Link>

      <Link href="/exercises/bench-press"
        className="flex h-14 w-full max-w-64 items-center justify-center rounded-lg bg-blue-400 px-4 text-center text-white transition-all duration-200 ease-out will-change-transform hover:-translate-y-1 hover:bg-sky-300 hover:shadow-[0_12px_30px_rgba(96,165,250,0.35)] active:translate-y-0 active:scale-[0.98] xl:h-16 xl:max-w-72 xl:text-xl">
        Bench Press
      </Link>

      <Link href="/exercises/bent-over-barbell-row"
        className="flex h-14 w-full max-w-64 items-center justify-center rounded-lg bg-blue-400 px-4 text-center text-white transition-all duration-200 ease-out will-change-transform hover:-translate-y-1 hover:bg-sky-300 hover:shadow-[0_12px_30px_rgba(96,165,250,0.35)] active:translate-y-0 active:scale-[0.98] xl:h-16 xl:max-w-72 xl:text-xl">
        Bent-over Barbell Row
      </Link>
    </div>
  )
}
