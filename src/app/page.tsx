"use client";

import Image from "next/image";
import AssetSearchComponent from "./components/AssetSearch";
import { motion, easeOut, TargetAndTransition } from "framer-motion";
import { Manrope } from "next/font/google";
import { motion, easeOut, TargetAndTransition } from "framer-motion";

const manrope = Manrope({ subsets: ["latin"], weight: ["400", "200"] });

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: (i = 1) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.15, duration: 0.5, ease: easeOut },
  }
  )
  }),
};

export default function Home() {

  return (

    <div className="font-sans grid grid-rows-[5vh_1fr_5vh] items-center justify-items-center min-h-screen p-[5vw] pb-[10vh] gap-[5vh]">
      <main className="flex flex-col gap-[4vh] row-start-2 items-center max-w-screen-md w-[90vw]">
        <motion.div
          className="dark:invert"

    <div
      className={`${manrope.className} grid grid-rows-[5vh_1fr_5vh] items-center justify-items-center min-h-screen p-[5vw] pb-[10vh] gap-[5vh]`}
    >
      <div className="flex flex-col gap-[4vh] row-start-2 items-center w-full">
        <motion.div

          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >

          <Image src="/next.svg" alt="Next.js logo" width={180} height={38} priority />

          <h1 className="text-7xl font-semibold text-white w-full flex items-center justify-center whitespace-nowrap ml-18">
            Welcome to{" "}
            <svg
              width="auto"
              height="90"
              viewBox="0 0 400 80"
              className="inline align-middle"
            >
              <defs>
                <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#0044d6ff" />
                  <stop offset="100%" stopColor="#02afffff" />
                </linearGradient>
              </defs>
              <text
                x="-16"
                y="64"
                fontSize="68"
                fontWeight="bold"
                fill="url(#grad1)"
              >
                HyJacked
              </text>
            </svg>
          </h1>

        </motion.div>

        <motion.ol
          className="font-mono list-inside list-decimal text-[clamp(0.8rem,2vw,1rem)] text-center leading-snug sm:text-left"
          variants={fadeIn}
          initial="hidden"
          animate="visible"
        >

          <motion.li className="mb-2 tracking-tight" custom={1} variants={fadeIn}>

          <motion.li
            className="mb-2 tracking-tight"
            custom={1}
            variants={fadeIn}
          >

            Get started by editing{" "}
            <code className="bg-black/[.05] dark:bg-white/[.06] font-mono font-semibold px-1 py-0.5 rounded">
              src/app/page.tsx
            </code>
            .
          </motion.li>
          <motion.li className="tracking-tight" custom={2} variants={fadeIn}>
            Save and see your changes instantly.
          </motion.li>
        </motion.ol>


        <motion.div initial="hidden" animate="visible" variants={fadeIn} custom={3}>

        <motion.div
          initial="hidden"
          animate="visible"
          variants={fadeIn}
          custom={3}
        >

          <AssetSearchComponent />
        </motion.div>

      </main>

      </div>


      <motion.footer
        className="row-start-3 flex gap-[2vw] flex-wrap items-center justify-center text-[clamp(0.8rem,1.5vw,0.95rem)]"
        initial="hidden"
        animate="visible"
        variants={fadeIn}
        custom={5}
      >
        
            {label}
          </motion.a>
        ))}
      </motion.footer>
    </div>
  );
}
