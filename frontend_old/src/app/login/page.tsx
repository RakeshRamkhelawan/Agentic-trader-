
"use client"

import { useAuth } from "@/context/auth-context"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Hexagon, LogIn } from "lucide-react"

export default function LoginPage() {
    const { login } = useAuth()

    return (
        <div className="flex min-h-screen items-center justify-center bg-background px-4">
            <Card className="w-full max-w-md text-center">
                <CardHeader className="space-y-4">
                    <div className="flex justify-center">
                        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                            <Hexagon className="h-8 w-8" strokeWidth={2.5} />
                        </div>
                    </div>
                    <CardTitle className="text-2xl">Welcome Back</CardTitle>
                    <CardDescription>
                        Sign in to Agentic Trader Platform to access your dashboard.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Button
                        onClick={() => login()}
                        className="w-full gap-2"
                        size="lg"
                    >
                        <LogIn className="h-5 w-5" />
                        Sign In with Auth0
                    </Button>
                </CardContent>
            </Card>
        </div>
    )
}
