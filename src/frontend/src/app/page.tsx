import Image from 'next/image'

export default function Home() {
  return (
    <main className="flex min-h-screen bg-blue-950 gap-8">
      <Title />
    </main>

  );
}


export function Title() {
  return (
    <div className="flex flex-col gap-10 ml-50 mt-70">
      <h1 className="text-white px-50 text-6xl font-extrabold">Welcome to <br />
        <span className="text-blue-200 p-20">Visual Spotter</span></h1>
      <div className="flex flex-row gap-20 ml-80">
        <Image
          src="/dumbbell.svg"
          width={100}
          height={100}
          alt="Dumbbell Icon"
        />
        <Image
          src="/weight.svg"
          width={100}
          height={100}
          alt="Weight Icon"
        />
      </div>
    </div>
  );
}
