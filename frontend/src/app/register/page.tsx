
"use client"

import { useAuth } from "@/context/auth-context"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Hexagon, UserPlus } from "lucide-react"
import Link from "next/link"

export default function RegisterPage() {
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
                    <CardTitle className="text-2xl">Create Account</CardTitle>
                    <CardDescription>
                        Join Agentic Trader Platform today.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Button
                        onClick={() => login()}
                        className="w-full gap-2"
                        size="lg"
                    >
                        <UserPlus className="h-5 w-5" />
                        Sign Up with Auth0
                    </Button>
                </CardContent>
                <CardFooter className="justify-center">
                    <div className="text-sm text-muted-foreground">
                        Already have an account?{" "}
                        <Link href="/login" className="underline hover:text-primary">
                            Login
                        </Link>
                    </div>
                </CardFooter>
            </Card>
        </div>
    )
}
