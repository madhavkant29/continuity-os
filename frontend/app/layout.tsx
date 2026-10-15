import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {title:"ContinuityOS — Operational resilience intelligence", description:"Graph-native business continuity simulations and provable recovery planning."};
export default function RootLayout({children}:{children:React.ReactNode}) { return <html lang="en"><body>{children}</body></html> }
