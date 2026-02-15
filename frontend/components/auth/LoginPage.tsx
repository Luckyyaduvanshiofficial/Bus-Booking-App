/**
 * LoginPage — 3-state auth component for phone+OTP login.
 *
 * States:
 * 1. PHONE — Enter phone number → sends OTP
 * 2. OTP — Enter 6-digit code → verifies OTP
 * 3. REGISTER — (new users only) Complete name + email
 *
 * Uses React Hook Form + Zod for validation.
 * Calls useAuth store for API integration.
 */

"use client";

import { memo, useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Phone,
  ArrowLeft,
  Loader2,
  ShieldCheck,
  Bus,
  AlertCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";
import {
  phoneFormSchema,
  otpFormSchema,
  registerFormSchema,
  type PhoneFormData,
  type OtpFormData,
  type RegisterFormData,
} from "@/lib/validations/auth";

type AuthStep = "phone" | "otp" | "register";

const RESEND_COOLDOWN_SECONDS = 30;

export const LoginPage = memo(function LoginPage() {
  const router = useRouter();
  const { sendOtp, verifyOtp, register, isLoading } = useAuth();

  const [step, setStep] = useState<AuthStep>("phone");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [resendTimer, setResendTimer] = useState(0);

  // OTP input refs for auto-focus
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  /* ── Resend countdown timer ────────────────────────── */

  const startResendTimer = useCallback(() => {
    setResendTimer(RESEND_COOLDOWN_SECONDS);
    timerRef.current = setInterval(() => {
      setResendTimer((prev) => {
        if (prev <= 1) {
          if (timerRef.current) clearInterval(timerRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }, []);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  /* ── Phone Form ────────────────────────────────────── */

  const phoneForm = useForm<PhoneFormData>({
    resolver: zodResolver(phoneFormSchema),
    defaultValues: { phone: "" },
  });

  const handleSendOtp = useCallback(
    async (data: PhoneFormData) => {
      setError(null);
      try {
        await sendOtp(data.phone);
        setPhone(data.phone);
        setStep("otp");
        startResendTimer();
      } catch (err: unknown) {
        setError(
          err instanceof Error ? err.message : "Failed to send OTP"
        );
      }
    },
    [sendOtp, startResendTimer]
  );

  /* ── OTP Form ──────────────────────────────────────── */

  const otpForm = useForm<OtpFormData>({
    resolver: zodResolver(otpFormSchema),
    defaultValues: { otp: "" },
  });

  const [otpDigits, setOtpDigits] = useState<string[]>(
    Array(6).fill("")
  );

  const handleOtpChange = useCallback(
    (index: number, value: string) => {
      if (value.length > 1) {
        // Handle paste
        const digits = value.replace(/\D/g, "").slice(0, 6).split("");
        const newOtpDigits = [...otpDigits];
        digits.forEach((d, i) => {
          if (index + i < 6) newOtpDigits[index + i] = d;
        });
        setOtpDigits(newOtpDigits);
        otpForm.setValue("otp", newOtpDigits.join(""));

        // Focus the next empty input or the last filled one
        const nextIndex = Math.min(index + digits.length, 5);
        otpRefs.current[nextIndex]?.focus();
        return;
      }

      const digit = value.replace(/\D/g, "");
      const newOtpDigits = [...otpDigits];
      newOtpDigits[index] = digit;
      setOtpDigits(newOtpDigits);
      otpForm.setValue("otp", newOtpDigits.join(""));

      // Auto-advance focus
      if (digit && index < 5) {
        otpRefs.current[index + 1]?.focus();
      }
    },
    [otpDigits, otpForm]
  );

  const handleOtpKeyDown = useCallback(
    (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Backspace" && !otpDigits[index] && index > 0) {
        otpRefs.current[index - 1]?.focus();
      }
    },
    [otpDigits]
  );

  const handleVerifyOtp = useCallback(
    async (data: OtpFormData) => {
      setError(null);
      try {
        const result = await verifyOtp(phone, data.otp);
        if (result.isNewUser) {
          setStep("register");
        } else {
          router.push("/");
        }
      } catch (err: unknown) {
        setError(
          err instanceof Error ? err.message : "Invalid OTP"
        );
        // Clear OTP inputs on error
        setOtpDigits(Array(6).fill(""));
        otpForm.setValue("otp", "");
        otpRefs.current[0]?.focus();
      }
    },
    [verifyOtp, phone, router, otpForm]
  );

  const handleResendOtp = useCallback(async () => {
    if (resendTimer > 0) return;
    setError(null);
    try {
      await sendOtp(phone);
      startResendTimer();
      setOtpDigits(Array(6).fill(""));
      otpForm.setValue("otp", "");
      otpRefs.current[0]?.focus();
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to resend OTP"
      );
    }
  }, [phone, resendTimer, sendOtp, startResendTimer, otpForm]);

  /* ── Register Form ─────────────────────────────────── */

  const registerForm = useForm<RegisterFormData>({
    resolver: zodResolver(registerFormSchema),
    defaultValues: { name: "", email: "" },
  });

  const handleRegister = useCallback(
    async (data: RegisterFormData) => {
      setError(null);
      try {
        await register({ phone, ...data });
        router.push("/");
      } catch (err: unknown) {
        setError(
          err instanceof Error ? err.message : "Registration failed"
        );
      }
    },
    [register, phone, router]
  );

  /* ── Render ────────────────────────────────────────── */

  return (
    <div className="flex min-h-[calc(100vh-80px)] items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md rounded-2xl shadow-md">
        {/* ── Brand Header ────────────────────────────── */}
        <CardHeader className="space-y-4 pb-2 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-blue/10">
            <Bus className="h-7 w-7 text-brand-blue" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              {step === "phone" && "Welcome to BusBook"}
              {step === "otp" && "Verify Your Phone"}
              {step === "register" && "Complete Your Profile"}
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              {step === "phone" &&
                "Enter your phone number to get started"}
              {step === "otp" &&
                `We sent a 6-digit code to +91 ${phone}`}
              {step === "register" &&
                "Just a few more details to set up your account"}
            </p>
          </div>
        </CardHeader>

        <CardContent className="px-6 pb-8 pt-4">
          {/* ── Error Message ───────────────────── */}
          {error && (
            <div className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* ── Step 1: Phone Input ─────────────── */}
          {step === "phone" && (
            <form
              onSubmit={phoneForm.handleSubmit(handleSendOtp)}
              className="space-y-5"
            >
              <div className="space-y-2">
                <Label htmlFor="phone" className="text-sm font-medium text-slate-700">
                  Phone Number
                </Label>
                <div className="flex">
                  <div className="flex items-center rounded-l-lg border border-r-0 border-slate-200 bg-slate-50 px-3 text-sm text-slate-600">
                    +91
                  </div>
                  <Input
                    id="phone"
                    type="tel"
                    inputMode="numeric"
                    placeholder="98765 43210"
                    maxLength={10}
                    className="rounded-l-none rounded-r-lg"
                    autoFocus
                    aria-label="Enter your 10-digit mobile number"
                    {...phoneForm.register("phone")}
                  />
                </div>
                {phoneForm.formState.errors.phone && (
                  <p className="text-xs text-red-500">
                    {phoneForm.formState.errors.phone.message}
                  </p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full rounded-xl bg-brand-orange text-white hover:bg-brand-orange/90"
                size="lg"
                disabled={isLoading}
                aria-label="Send OTP to your phone"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Sending OTP...
                  </>
                ) : (
                  <>
                    <Phone className="h-4 w-4" />
                    Send OTP
                  </>
                )}
              </Button>

              {/* Trust badge */}
              <div className="flex items-center justify-center gap-1.5 text-xs text-slate-400">
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>Your number is safe and never shared</span>
              </div>
            </form>
          )}

          {/* ── Step 2: OTP Verification ────────── */}
          {step === "otp" && (
            <form
              onSubmit={otpForm.handleSubmit(handleVerifyOtp)}
              className="space-y-5"
            >
              {/* Back button */}
              <button
                type="button"
                onClick={() => {
                  setStep("phone");
                  setError(null);
                  setOtpDigits(Array(6).fill(""));
                  otpForm.setValue("otp", "");
                }}
                className="flex items-center gap-1 text-sm text-brand-blue hover:underline"
                aria-label="Go back to phone number input"
              >
                <ArrowLeft className="h-4 w-4" />
                Change number
              </button>

              {/* OTP Digit Inputs */}
              <div className="space-y-2">
                <Label className="text-sm font-medium text-slate-700">
                  Enter OTP
                </Label>
                <div className="flex justify-between gap-2">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <Input
                      key={i}
                      ref={(el) => {
                        otpRefs.current[i] = el;
                      }}
                      type="text"
                      inputMode="numeric"
                      maxLength={6}
                      value={otpDigits[i]}
                      onChange={(e) =>
                        handleOtpChange(i, e.target.value)
                      }
                      onKeyDown={(e) => handleOtpKeyDown(i, e)}
                      className="h-12 w-12 rounded-lg text-center text-lg font-semibold"
                      autoFocus={i === 0}
                      aria-label={`OTP digit ${i + 1}`}
                    />
                  ))}
                </div>
                {otpForm.formState.errors.otp && (
                  <p className="text-xs text-red-500">
                    {otpForm.formState.errors.otp.message}
                  </p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full rounded-xl bg-brand-orange text-white hover:bg-brand-orange/90"
                size="lg"
                disabled={
                  isLoading || otpDigits.join("").length < 6
                }
                aria-label="Verify OTP"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  "Verify OTP"
                )}
              </Button>

              {/* Resend OTP */}
              <div className="text-center text-sm text-slate-500">
                {resendTimer > 0 ? (
                  <span>
                    Resend OTP in{" "}
                    <span className="font-medium text-brand-blue">
                      {resendTimer}s
                    </span>
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={handleResendOtp}
                    disabled={isLoading}
                    className="font-medium text-brand-blue hover:underline disabled:opacity-50"
                    aria-label="Resend OTP"
                  >
                    Resend OTP
                  </button>
                )}
              </div>
            </form>
          )}

          {/* ── Step 3: Registration ────────────── */}
          {step === "register" && (
            <form
              onSubmit={registerForm.handleSubmit(handleRegister)}
              className="space-y-5"
            >
              <div className="space-y-2">
                <Label htmlFor="name" className="text-sm font-medium text-slate-700">
                  Full Name
                </Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="Your full name"
                  autoFocus
                  aria-label="Enter your full name"
                  {...registerForm.register("name")}
                />
                {registerForm.formState.errors.name && (
                  <p className="text-xs text-red-500">
                    {registerForm.formState.errors.name.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-medium text-slate-700">
                  Email Address
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  aria-label="Enter your email address"
                  {...registerForm.register("email")}
                />
                {registerForm.formState.errors.email && (
                  <p className="text-xs text-red-500">
                    {registerForm.formState.errors.email.message}
                  </p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full rounded-xl bg-brand-orange text-white hover:bg-brand-orange/90"
                size="lg"
                disabled={isLoading}
                aria-label="Complete registration"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating Account...
                  </>
                ) : (
                  "Get Started"
                )}
              </Button>

              <p className="text-center text-xs text-slate-400">
                By continuing, you agree to our{" "}
                <a href="/terms" className="text-brand-blue hover:underline">
                  Terms
                </a>{" "}
                and{" "}
                <a href="/privacy" className="text-brand-blue hover:underline">
                  Privacy Policy
                </a>
              </p>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
});
