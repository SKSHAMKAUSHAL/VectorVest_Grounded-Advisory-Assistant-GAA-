import { describe, it, expect } from "vitest";
import { signInSchema, signUpSchema } from "../components/AuthModule";

describe("Authentication Form Validation Unit Tests", () => {
  describe("Sign In Schema Validation", () => {
    it("should fail validation when submitting empty Sign In form", () => {
      const result = signInSchema.safeParse({ email: "", password: "" });
      expect(result.success).toBe(false);
      if (!result.success) {
        const errorMap = result.error.flatten().fieldErrors;
        expect(errorMap.email).toBeDefined();
        expect(errorMap.password).toBeDefined();
      }
    });

    it("should display error for invalid email formats", () => {
      const invalidEmails = ["plainaddress", "missing@domain", "@nodomain.com", "spaces in@email.com"];
      for (const email of invalidEmails) {
        const result = signInSchema.safeParse({ email, password: "Password123!" });
        expect(result.success).toBe(false);
        if (!result.success) {
          expect(result.error.flatten().fieldErrors.email?.[0]).toContain("valid email");
        }
      }
    });

    it("should pass validation for valid email and password", () => {
      const result = signInSchema.safeParse({
        email: "rm@wealth.bank.com",
        password: "AdvisoryPass2024!",
        rememberMe: true,
      });
      expect(result.success).toBe(true);
    });
  });

  describe("Sign Up Schema Validation", () => {
    it("should fail validation when submitting empty Sign Up form", () => {
      const result = signUpSchema.safeParse({
        fullName: "",
        email: "",
        password: "",
        confirmPassword: "",
        termsAccepted: false,
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        const errors = result.error.flatten().fieldErrors;
        expect(errors.fullName).toBeDefined();
        expect(errors.email).toBeDefined();
        expect(errors.password).toBeDefined();
        expect(errors.termsAccepted).toBeDefined();
      }
    });

    it("should reject full names with special characters or numbers", () => {
      const invalidNames = ["Jane123", "John_Doe", "A"];
      for (const fullName of invalidNames) {
        const result = signUpSchema.safeParse({
          fullName,
          email: "jane@bank.com",
          password: "SecurePassword1!",
          confirmPassword: "SecurePassword1!",
          termsAccepted: true,
        });
        expect(result.success).toBe(false);
      }
    });

    it("should enforce strong password rules (uppercase, lowercase, number, special char, min 8 chars)", () => {
      const weakPasswords = [
        "short1!",        // < 8 chars
        "nouppercase1!",  // missing uppercase
        "NOLOWERCASE1!",  // missing lowercase
        "NoSpecialChar1", // missing symbol
        "NoNumbersHere!", // missing number
      ];

      for (const password of weakPasswords) {
        const result = signUpSchema.safeParse({
          fullName: "Jane Doe",
          email: "jane@bank.com",
          password,
          confirmPassword: password,
          termsAccepted: true,
        });
        expect(result.success).toBe(false);
      }
    });

    it("should throw error if confirmPassword does not match password", () => {
      const result = signUpSchema.safeParse({
        fullName: "Jane Doe",
        email: "jane@bank.com",
        password: "SecurePassword1!",
        confirmPassword: "DifferentPassword1!",
        termsAccepted: true,
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.flatten().fieldErrors.confirmPassword?.[0]).toBe("Passwords do not match");
      }
    });

    it("should pass validation for fully compliant registration data", () => {
      const result = signUpSchema.safeParse({
        fullName: "Jane Doe",
        email: "jane.doe@wealth.bank.com",
        password: "SecurePassword1!",
        confirmPassword: "SecurePassword1!",
        termsAccepted: true,
      });
      expect(result.success).toBe(true);
    });
  });
});
