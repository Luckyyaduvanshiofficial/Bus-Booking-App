/**
 * Zod validation schemas for authentication forms.
 *
 * - phoneSchema: Indian mobile number (10 digits after stripping +91)
 * - otpSchema: exactly 6 digits
 * - registerSchema: name (2-50 chars) + valid email + phone
 */

import { z } from "zod";

/** Strip leading +91 or 91 and validate 10-digit Indian mobile number. */
export const phoneSchema = z
  .string()
  .trim()
  .transform((val) => val.replace(/^(\+91|91)/, "").replace(/\s/g, ""))
  .pipe(
    z
      .string()
      .length(10, "Phone number must be exactly 10 digits")
      .regex(/^\d{10}$/, "Phone number must contain only digits")
  );

/** 6-digit OTP code. */
export const otpSchema = z
  .string()
  .length(6, "OTP must be 6 digits")
  .regex(/^\d{6}$/, "OTP must contain only digits");

/** Phone input form — Step 1 of login flow. */
export const phoneFormSchema = z.object({
  phone: phoneSchema,
});

/** OTP verification form — Step 2 of login flow. */
export const otpFormSchema = z.object({
  otp: otpSchema,
});

/** Registration form — Step 3 (only for new users). */
export const registerFormSchema = z.object({
  name: z
    .string()
    .trim()
    .min(2, "Name must be at least 2 characters")
    .max(50, "Name must be under 50 characters"),
  email: z
    .string()
    .trim()
    .email("Please enter a valid email address"),
});

export type PhoneFormData = z.infer<typeof phoneFormSchema>;
export type OtpFormData = z.infer<typeof otpFormSchema>;
export type RegisterFormData = z.infer<typeof registerFormSchema>;
