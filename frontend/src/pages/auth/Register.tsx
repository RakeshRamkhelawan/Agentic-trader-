import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Eye, EyeOff, Mail, Lock, User, Zap, ArrowRight, ArrowLeft, Loader2, Check } from 'lucide-react';
import { useAuth0 } from '@auth0/auth0-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';

export function Register() {
  const { loginWithRedirect, isLoading: isAuth0Loading } = useAuth0();
  const [error, setError] = useState<string | null>(null);
  
  const [step, setStep] = useState(1);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // Form Data
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    agreedToTerms: false,
    agreedToPrivacy: false,
    marketingConsent: false,
  });

  const updateField = (field: string, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
  };

  const validateStep = () => {
    switch (step) {
      case 1:
        return formData.firstName && formData.lastName;
      case 2:
        return formData.email && formData.password && formData.password.length >= 8;
      case 3:
        return formData.agreedToTerms && formData.agreedToPrivacy;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (step < 3) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleSubmit = async () => {
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    // Use Auth0 signup with redirect
    await loginWithRedirect({
      authorizationParams: {
        screen_hint: 'signup',
      },
    });
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-4 animate-fade-in">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="firstName" className="text-white">First Name</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="firstName"
                    placeholder="John"
                    value={formData.firstName}
                    onChange={(e) => updateField('firstName', e.target.value)}
                    className="pl-10 bg-[#0A0A0A] border-[#262626] text-white placeholder:text-muted-foreground focus:border-trade-blue"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="lastName" className="text-white">Last Name</Label>
                <Input
                  id="lastName"
                  placeholder="Doe"
                  value={formData.lastName}
                  onChange={(e) => updateField('lastName', e.target.value)}
                  className="bg-[#0A0A0A] border-[#262626] text-white placeholder:text-muted-foreground focus:border-trade-blue"
                />
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-4 animate-fade-in">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-white">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) => updateField('email', e.target.value)}
                  className="pl-10 bg-[#0A0A0A] border-[#262626] text-white placeholder:text-muted-foreground focus:border-trade-blue"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-white">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => updateField('password', e.target.value)}
                  className="pl-10 pr-10 bg-[#0A0A0A] border-[#262626] text-white placeholder:text-muted-foreground focus:border-trade-blue"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-xs text-muted-foreground">
                Must be at least 8 characters with uppercase, lowercase, and number
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-white">Confirm Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={formData.confirmPassword}
                  onChange={(e) => updateField('confirmPassword', e.target.value)}
                  className="pl-10 pr-10 bg-[#0A0A0A] border-[#262626] text-white placeholder:text-muted-foreground focus:border-trade-blue"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {formData.confirmPassword && formData.password !== formData.confirmPassword && (
                <p className="text-xs text-trade-red">Passwords do not match</p>
              )}
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-4 animate-fade-in">
            <div className="flex items-start gap-3 p-4 rounded-lg bg-[#0A0A0A] border border-[#262626]">
              <Checkbox
                id="terms"
                checked={formData.agreedToTerms}
                onCheckedChange={(checked) => updateField('agreedToTerms', checked as boolean)}
                className="mt-1 border-[#262626] data-[state=checked]:bg-trade-blue data-[state=checked]:border-trade-blue"
              />
              <div>
                <Label htmlFor="terms" className="text-white cursor-pointer">
                  I agree to the{' '}
                  <Link to="/terms" className="text-trade-blue hover:underline">Terms of Service</Link>
                </Label>
                <p className="text-xs text-muted-foreground mt-1">
                  By creating an account, you agree to our terms and conditions
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 rounded-lg bg-[#0A0A0A] border border-[#262626]">
              <Checkbox
                id="privacy"
                checked={formData.agreedToPrivacy}
                onCheckedChange={(checked) => updateField('agreedToPrivacy', checked as boolean)}
                className="mt-1 border-[#262626] data-[state=checked]:bg-trade-blue data-[state=checked]:border-trade-blue"
              />
              <div>
                <Label htmlFor="privacy" className="text-white cursor-pointer">
                  I agree to the{' '}
                  <Link to="/privacy" className="text-trade-blue hover:underline">Privacy Policy</Link>
                </Label>
                <p className="text-xs text-muted-foreground mt-1">
                  I understand how my data will be used and protected
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 rounded-lg bg-[#0A0A0A] border border-[#262626]">
              <Checkbox
                id="marketing"
                checked={formData.marketingConsent}
                onCheckedChange={(checked) => updateField('marketingConsent', checked as boolean)}
                className="mt-1 border-[#262626] data-[state=checked]:bg-trade-blue data-[state=checked]:border-trade-blue"
              />
              <div>
                <Label htmlFor="marketing" className="text-white cursor-pointer">
                  Send me marketing updates (optional)
                </Label>
                <p className="text-xs text-muted-foreground mt-1">
                  Get notified about new features, promotions, and market insights
                </p>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const stepTitles = ['Personal Info', 'Account Details', 'Terms & Conditions'];
  const progress = (step / 3) * 100;

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#000000] p-4">
      {/* Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-trade-blue/10 rounded-full blur-[128px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-trade-purple/10 rounded-full blur-[128px]" />
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo */}
        <div className="flex items-center justify-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-trade-blue to-trade-cyan flex items-center justify-center shadow-glow-blue">
            <Zap className="w-8 h-8 text-white" />
          </div>
        </div>

        <Card className="bg-[#111111] border-[#262626] shadow-2xl">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-white">Create Account</CardTitle>
            <CardDescription className="text-muted-foreground">
              Step {step} of 3: {stepTitles[step - 1]}
            </CardDescription>
            <Progress value={progress} className="mt-4 h-1 bg-[#262626]" />
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Error Message */}
            {error && (
              <div className="p-3 rounded-lg bg-trade-red/10 border border-trade-red/20 text-trade-red text-sm">
                {error}
              </div>
            )}

            {/* Step Content */}
            {renderStep()}

            {/* Navigation Buttons */}
            <div className="flex gap-3">
              {step > 1 && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleBack}
                  className="flex-1 border-[#262626] bg-transparent text-white hover:bg-[#1A1A1A]"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
              )}
              
              {step < 3 ? (
                <Button
                  type="button"
                  onClick={handleNext}
                  disabled={!validateStep()}
                  className="flex-1 bg-trade-blue hover:bg-trade-blue/90 text-white py-6 font-semibold shadow-glow-blue disabled:opacity-50"
                >
                  Continue
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              ) : (
                <Button
                  type="button"
                  onClick={handleSubmit}
                  disabled={!validateStep() || isAuth0Loading || formData.password !== formData.confirmPassword}
                  className="flex-1 bg-trade-green hover:bg-trade-green/90 text-white py-6 font-semibold shadow-glow-green disabled:opacity-50"
                >
                  {isAuth0Loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      Create Account
                      <Check className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              )}
            </div>

            <Separator className="bg-[#262626]" />

            {/* Social Sign Up */}
            <div className="space-y-3">
              <p className="text-center text-sm text-muted-foreground">Or sign up with</p>
              <div className="grid grid-cols-2 gap-3">
                <Button
                  variant="outline"
                  className="border-[#262626] bg-transparent text-white hover:bg-[#1A1A1A]"
                >
                  <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Google
                </Button>
                <Button
                  variant="outline"
                  className="border-[#262626] bg-transparent text-white hover:bg-[#1A1A1A]"
                >
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
                  </svg>
                  GitHub
                </Button>
              </div>
            </div>

            {/* Login Link */}
            <p className="text-center text-sm text-muted-foreground">
              Already have an account?{' '}
              <Link to="/login" className="text-trade-blue hover:underline font-medium">
                Sign in
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
