import Link from "next/dist/client/link";
import Image from "next/image";

export default function FormChecker_Button({ path }: { path: string }) {
    return (
        <Link href={`${path}`}
            className="flex h-14 w-full max-w-64 items-center justify-center gap-2 rounded-lg bg-blue-400 px-4 text-center text-white transition-all duration-200 ease-out will-change-transform hover:-translate-y-1 hover:bg-sky-300 hover:shadow-[0_12px_30px_rgba(96,165,250,0.35)] active:translate-y-0 active:scale-[0.98] xl:h-16 xl:max-w-72 xl:text-xl">
            <Image
                src="/formCheckerIcon.svg"
                width={30}
                height={30}
                className="h-9 w-9 shrink-0"
                alt="Weight Icon"
            />
            <span>Open Form Checker</span>
        </Link>
    )
}