import { useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useAppStore } from '@/store/appStore';

export function useAuth() {
  const { 
    user, 
    isAuthenticated, 
    isLoading, 
    error,
    kycData,
    login, 
    logout, 
    register,
    clearError 
  } = useAuthStore();

  const { setUser } = useAppStore();

  // Sync auth user with app store
  useEffect(() => {
    if (user && isAuthenticated) {
      setUser({
        id: user.id,
        email: user.email,
        displayName: user.displayName,
        avatar: user.avatar,
      });
    } else {
      setUser(null);
    }
  }, [user, isAuthenticated, setUser]);

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    kycStatus: kycData?.status || 'not_started',
    isKYCDone: kycData?.status === 'verified',
    isKYCPending: kycData?.status === 'pending_review' || kycData?.status === 'in_progress',
    login,
    logout,
    register,
    clearError,
  };
}

export function useRequireAuth() {
  const { isAuthenticated, isLoading } = useAuthStore();

  return {
    isAuthenticated,
    isLoading,
    requireAuth: !isAuthenticated && !isLoading,
  };
}

export function useOnboarding() {
  const {
    onboardingStep,
    onboardingData,
    kycStep,
    kycData,
    setOnboardingStep,
    updateOnboardingData,
    completeOnboarding,
    setKYCStep,
    updateKYCData,
    submitKYC,
  } = useAuthStore();

  return {
    onboardingStep,
    onboardingData,
    kycStep,
    kycData,
    setOnboardingStep,
    updateOnboardingData,
    completeOnboarding,
    setKYCStep,
    updateKYCData,
    submitKYC,
    totalOnboardingSteps: 3,
    totalKYCSteps: 4,
  };
}
