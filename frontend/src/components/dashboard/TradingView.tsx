"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export const TradingView = () => {
    return (
        <Card className="h-[600px] w-full">
            <CardHeader>
                <CardTitle>Professional Chart (Placeholder)</CardTitle>
            </CardHeader>
            <CardContent className="flex items-center justify-center h-[500px] bg-muted/20">
                <div className="text-center space-y-2">
                    <p className="text-lg font-medium">Chart Loading...</p>
                    <p className="text-sm text-muted-foreground">Detailed market analysis chart will appear here</p>
                </div>
            </CardContent>
        </Card>
    )
}
