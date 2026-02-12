
"use client";

import { useAuth0 } from "@auth0/auth0-react";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function CallbackPage() {
    const { error } = useAuth0();
    const router = useRouter();

    useEffect(() => {
        if (error) {
            console.error("Auth0 Callback Error:", error);
            // Optionally redirect to login or error page
            router.push("/login");
        }
    }, [error, router]);

    return (
        <div className="flex h-screen w-full items-center justify-center">
            <div className="flex flex-col items-center gap-4">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-muted-foreground">Completing secure sign-in...</p>
            </div>
        </div>
    );
}
