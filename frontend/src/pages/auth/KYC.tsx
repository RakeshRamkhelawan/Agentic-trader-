import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  User, 
  MapPin, 
  CreditCard, 
  Briefcase, 
  Camera, 
  Upload, 
  Check, 
  ArrowRight, 
  ArrowLeft, 
  Loader2,
  Shield,
  AlertCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUserStore } from '@/store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';

const countries = [
  'United States', 'United Kingdom', 'Canada', 'Australia', 'Germany', 
  'France', 'Netherlands', 'Switzerland', 'Singapore', 'Japan', 'Other'
];

const occupations = [
  'Employed', 'Self-employed', 'Student', 'Retired', 'Unemployed', 'Other'
];

const incomeRanges = [
  'Under $25,000', '$25,000 - $50,000', '$50,000 - $100,000', 
  '$100,000 - $250,000', 'Over $250,000'
];

const idTypes = [
  { value: 'passport', label: 'Passport' },
  { value: 'drivers_license', label: "Driver's License" },
  { value: 'national_id', label: 'National ID Card' },
];

export function KYC() {
  const navigate = useNavigate();
  const { kycData, updateKYCData, submitKYC, kycIsLoading: isLoading } = useUserStore();
  
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    // Personal Info
    firstName: kycData?.firstName || '',
    lastName: kycData?.lastName || '',
    dateOfBirth: kycData?.dateOfBirth || '',
    nationality: kycData?.nationality || '',
    phoneNumber: kycData?.phoneNumber || '',
    
    // Address
    streetAddress: kycData?.streetAddress || '',
    city: kycData?.city || '',
    postalCode: kycData?.postalCode || '',
    country: kycData?.country || '',
    
    // Identity
    idType: kycData?.idType || '',
    idNumber: kycData?.idNumber || '',
    
    // Financial
    occupation: kycData?.occupation || '',
    employmentStatus: kycData?.employmentStatus || '',
    annualIncome: kycData?.annualIncome || '',
    sourceOfFunds: kycData?.sourceOfFunds || '',
  });

  const [uploadedFiles, setUploadedFiles] = useState<{
    front?: string;
    back?: string;
    selfie?: string;
  }>({});

  const updateField = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    updateKYCData({ [field]: value });
  };

  const handleFileUpload = (type: 'front' | 'back' | 'selfie') => {
    // Simulate file upload
    setUploadedFiles(prev => ({ ...prev, [type]: `uploaded_${type}.jpg` }));
  };

  const validateStep = () => {
    switch (step) {
      case 1:
        return formData.firstName && formData.lastName && formData.dateOfBirth && 
               formData.nationality && formData.phoneNumber;
      case 2:
        return formData.streetAddress && formData.city && formData.postalCode && formData.country;
      case 3:
        return formData.idType && formData.idNumber && uploadedFiles.front;
      case 4:
        return formData.occupation && formData.annualIncome && formData.sourceOfFunds;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (step < 4) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleSubmit = async () => {
    const success = await submitKYC();
    if (success) {
      navigate('/dashboard');
    }
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-4 animate-fade-in">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-white">First Name</Label>
                <Input
                  value={formData.firstName}
                  onChange={(e) => updateField('firstName', e.target.value)}
                  className="bg-[#0A0A0A] border-[#262626] text-white"
                  placeholder="John"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-white">Last Name</Label>
                <Input
                  value={formData.lastName}
                  onChange={(e) => updateField('lastName', e.target.value)}
                  className="bg-[#0A0A0A] border-[#262626] text-white"
                  placeholder="Doe"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-white">Date of Birth</Label>
              <Input
                type="date"
                value={formData.dateOfBirth}
                onChange={(e) => updateField('dateOfBirth', e.target.value)}
                className="bg-[#0A0A0A] border-[#262626] text-white"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-white">Nationality</Label>
              <Select value={formData.nationality} onValueChange={(v) => updateField('nationality', v)}>
                <SelectTrigger className="bg-[#0A0A0A] border-[#262626] text-white">
                  <SelectValue placeholder="Select nationality" />
                </SelectTrigger>
                <SelectContent className="bg-[#111111] border-[#262626]">
                  {countries.map(c => (
                    <SelectItem key={c} value={c} className="text-white">{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-white">Phone Number</Label>
              <Input
                value={formData.phoneNumber}
                onChange={(e) => updateField('phoneNumber', e.target.value)}
                className="bg-[#0A0A0A] border-[#262626] text-white"
                placeholder="+1 (555) 000-0000"
              />
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-4 animate-fade-in">
            <div className="space-y-2">
              <Label className="text-white">Street Address</Label>
              <Input
                value={formData.streetAddress}
                onChange={(e) => updateField('streetAddress', e.target.value)}
                className="bg-[#0A0A0A] border-[#262626] text-white"
                placeholder="123 Main Street, Apt 4B"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-white">City</Label>
                <Input
                  value={formData.city}
                  onChange={(e) => updateField('city', e.target.value)}
                  className="bg-[#0A0A0A] border-[#262626] text-white"
                  placeholder="New York"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-white">Postal Code</Label>
                <Input
                  value={formData.postalCode}
                  onChange={(e) => updateField('postalCode', e.target.value)}
                  className="bg-[#0A0A0A] border-[#262626] text-white"
                  placeholder="10001"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-white">Country</Label>
              <Select value={formData.country} onValueChange={(v) => updateField('country', v)}>
                <SelectTrigger className="bg-[#0A0A0A] border-[#262626] text-white">
                  <SelectValue placeholder="Select country" />
                </SelectTrigger>
                <SelectContent className="bg-[#111111] border-[#262626]">
                  {countries.map(c => (
                    <SelectItem key={c} value={c} className="text-white">{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-4 animate-fade-in">
            <div className="space-y-2">
              <Label className="text-white">ID Type</Label>
              <Select value={formData.idType} onValueChange={(v) => updateField('idType', v as any)}>
                <SelectTrigger className="bg-[#0A0A0A] border-[#262626] text-white">
                  <SelectValue placeholder="Select ID type" />
                </SelectTrigger>
                <SelectContent className="bg-[#111111] border-[#262626]">
                  {idTypes.map(t => (
                    <SelectItem key={t.value} value={t.value} className="text-white">{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-white">ID Number</Label>
              <Input
                value={formData.idNumber}
                onChange={(e) => updateField('idNumber', e.target.value)}
                className="bg-[#0A0A0A] border-[#262626] text-white"
                placeholder="Enter your ID number"
              />
            </div>

            <Separator className="bg-[#262626]" />

            <p className="text-sm text-muted-foreground">Upload Documents</p>

            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => handleFileUpload('front')}
                className={cn(
                  'p-4 rounded-xl border-2 border-dashed transition-all',
                  uploadedFiles.front 
                    ? 'border-trade-green bg-trade-green/10' 
                    : 'border-[#262626] hover:border-[#333333] bg-[#0A0A0A]'
                )}
              >
                <Upload className={cn(
                  'w-8 h-8 mx-auto mb-2',
                  uploadedFiles.front ? 'text-trade-green' : 'text-muted-foreground'
                )} />
                <p className="text-sm text-white">ID Front</p>
                {uploadedFiles.front && <Check className="w-4 h-4 text-trade-green mx-auto mt-1" />}
              </button>

              <button
                onClick={() => handleFileUpload('back')}
                className={cn(
                  'p-4 rounded-xl border-2 border-dashed transition-all',
                  uploadedFiles.back 
                    ? 'border-trade-green bg-trade-green/10' 
                    : 'border-[#262626] hover:border-[#333333] bg-[#0A0A0A]'
                )}
              >
                <Upload className={cn(
                  'w-8 h-8 mx-auto mb-2',
                  uploadedFiles.back ? 'text-trade-green' : 'text-muted-foreground'
                )} />
                <p className="text-sm text-white">ID Back</p>
                {uploadedFiles.back && <Check className="w-4 h-4 text-trade-green mx-auto mt-1" />}
              </button>
            </div>

            <button
              onClick={() => handleFileUpload('selfie')}
              className={cn(
                'w-full p-4 rounded-xl border-2 border-dashed transition-all',
                uploadedFiles.selfie 
                  ? 'border-trade-green bg-trade-green/10' 
                  : 'border-[#262626] hover:border-[#333333] bg-[#0A0A0A]'
              )}
            >
              <Camera className={cn(
                'w-8 h-8 mx-auto mb-2',
                uploadedFiles.selfie ? 'text-trade-green' : 'text-muted-foreground'
              )} />
              <p className="text-sm text-white">Selfie with ID</p>
              {uploadedFiles.selfie && <Check className="w-4 h-4 text-trade-green mx-auto mt-1" />}
            </button>
          </div>
        );

      case 4:
        return (
          <div className="space-y-4 animate-fade-in">
            <div className="space-y-2">
              <Label className="text-white">Occupation</Label>
              <Select value={formData.occupation} onValueChange={(v) => updateField('occupation', v)}>
                <SelectTrigger className="bg-[#0A0A0A] border-[#262626] text-white">
                  <SelectValue placeholder="Select occupation" />
                </SelectTrigger>
                <SelectContent className="bg-[#111111] border-[#262626]">
                  {occupations.map(o => (
                    <SelectItem key={o} value={o} className="text-white">{o}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-white">Annual Income</Label>
              <Select value={formData.annualIncome} onValueChange={(v) => updateField('annualIncome', v)}>
                <SelectTrigger className="bg-[#0A0A0A] border-[#262626] text-white">
                  <SelectValue placeholder="Select income range" />
                </SelectTrigger>
                <SelectContent className="bg-[#111111] border-[#262626]">
                  {incomeRanges.map(i => (
                    <SelectItem key={i} value={i} className="text-white">{i}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-white">Source of Funds</Label>
              <Input
                value={formData.sourceOfFunds}
                onChange={(e) => updateField('sourceOfFunds', e.target.value)}
                className="bg-[#0A0A0A] border-[#262626] text-white"
                placeholder="e.g., Salary, Investments, Business"
              />
            </div>

            <div className="p-4 rounded-lg bg-trade-blue/10 border border-trade-blue/20">
              <div className="flex items-start gap-3">
                <Shield className="w-5 h-5 text-trade-blue flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-white font-medium">Your data is secure</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    We use bank-level encryption to protect your personal information. 
                    Your data will only be used for identity verification purposes.
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const stepIcons = [User, MapPin, CreditCard, Briefcase];
  const stepTitles = ['Personal Info', 'Address', 'Identity', 'Financial'];
  const progress = (step / 4) * 100;

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#000000] p-4">
      {/* Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-trade-blue/10 rounded-full blur-[128px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-trade-purple/10 rounded-full blur-[128px]" />
      </div>

      <div className="w-full max-w-lg relative z-10">
        {/* Logo */}
        <div className="flex items-center justify-center mb-6">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-trade-blue to-trade-cyan flex items-center justify-center shadow-glow-blue">
            <Shield className="w-7 h-7 text-white" />
          </div>
        </div>

        <Card className="bg-[#111111] border-[#262626] shadow-2xl">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-white">Verify Your Identity</CardTitle>
            <CardDescription className="text-muted-foreground">
              Complete KYC verification to start trading
            </CardDescription>
            
            {/* Step Indicators */}
            <div className="flex items-center justify-center gap-2 mt-4">
              {[1, 2, 3, 4].map((s) => {
                const Icon = stepIcons[s - 1];
                return (
                  <div
                    key={s}
                    className={cn(
                      'w-10 h-10 rounded-xl flex items-center justify-center transition-all',
                      s === step 
                        ? 'bg-trade-blue text-white shadow-glow-blue' 
                        : s < step 
                          ? 'bg-trade-green/20 text-trade-green' 
                          : 'bg-[#0A0A0A] text-muted-foreground'
                    )}
                  >
                    {s < step ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                  </div>
                );
              })}
            </div>
            
            <Progress value={progress} className="mt-4 h-1 bg-[#262626]" />
            <p className="text-sm text-muted-foreground mt-2">
              Step {step} of 4: {stepTitles[step - 1]}
            </p>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Step Content */}
            {renderStep()}

            {/* Navigation Buttons */}
            <div className="flex gap-3 pt-4">
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
              
              {step < 4 ? (
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
                  disabled={!validateStep() || isLoading}
                  className="flex-1 bg-trade-green hover:bg-trade-green/90 text-white py-6 font-semibold shadow-glow-green disabled:opacity-50"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      Submit Verification
                      <Check className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              )}
            </div>

            {/* Info Box */}
            <div className="flex items-start gap-3 p-3 rounded-lg bg-[#0A0A0A] border border-[#262626]">
              <AlertCircle className="w-5 h-5 text-trade-orange flex-shrink-0 mt-0.5" />
              <p className="text-xs text-muted-foreground">
                KYC verification is required by law for all trading platforms. 
                Verification typically takes 1-2 business days.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Skip for Demo */}
        <p className="text-center text-sm text-muted-foreground mt-6">
          <button 
            onClick={() => navigate('/dashboard')} 
            className="text-trade-blue hover:underline"
          >
            Skip for demo →
          </button>
        </p>
      </div>
    </div>
  );
}
