/**
 * PaperSessionControls Component
 * 
 * Controls for starting and stopping paper trading sessions.
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Play, Square, Wallet, Clock, Activity, Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import usePaperTradingStore from '@/store/paper-trading';

export function PaperSessionControls() {
  const {
    isRunning,
    isStarting,
    isStopping,
    error,
    sessionId,
    startedAt,
    config,
    startSession,
    stopSession,
    clearError,
  } = usePaperTradingStore();

  const [duration, setDuration] = useState(8);
  const [capital, setCapital] = useState(10000);

  const handleStart = async () => {
    clearError();
    try {
      await startSession({ duration, capital });
    } catch (err) {
      // Error is handled in store
    }
  };

  const handleStop = async () => {
    clearError();
    try {
      await stopSession();
    } catch (err) {
      // Error is handled in store
    }
  };

  if (isRunning) {
    return (
      <Card className="border-green-200 bg-green-50/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-green-500" />
                Session Active
                <Badge variant="default" className="bg-green-500">Live</Badge>
              </CardTitle>
              <CardDescription>
                {sessionId && `ID: ${sessionId.slice(0, 8)}...`}
              </CardDescription>
            </div>
            <Button
              variant="destructive"
              onClick={handleStop}
              disabled={isStopping}
              className="gap-2"
            >
              {isStopping ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Square className="h-4 w-4" />
              )}
              {isStopping ? 'Stopping...' : 'Stop Session'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="flex items-center gap-2">
              <Wallet className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Capital</p>
                <p className="font-semibold">
                  €{config?.capital.toLocaleString() || capital.toLocaleString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Duration</p>
                <p className="font-semibold">{config?.duration || duration} hours</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Started</p>
                <p className="font-semibold">
                  {startedAt ? new Date(startedAt).toLocaleTimeString() : '--:--'}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Play className="h-5 w-5" />
          Start Paper Trading
        </CardTitle>
        <CardDescription>
          Configure and start a new paper trading session
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="capital">Initial Capital (€)</Label>
            <Input
              id="capital"
              type="number"
              value={capital}
              onChange={(e) => setCapital(Number(e.target.value))}
              min={1000}
              step={1000}
              disabled={isStarting}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="duration">Duration (hours)</Label>
            <Input
              id="duration"
              type="number"
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              min={1}
              max={24}
              disabled={isStarting}
            />
          </div>
        </div>

        <Button
          onClick={handleStart}
          disabled={isStarting}
          className="w-full gap-2"
        >
          {isStarting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          {isStarting ? 'Starting...' : 'Start Session'}
        </Button>
      </CardContent>
    </Card>
  );
}

export default PaperSessionControls;
