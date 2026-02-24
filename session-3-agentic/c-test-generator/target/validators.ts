export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

export function validateEmail(email: string): ValidationResult {
  const errors: string[] = [];
  if (!email) errors.push('Email is required');
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.push('Invalid email format');
  return { valid: errors.length === 0, errors };
}

export function validatePassword(password: string): ValidationResult {
  const errors: string[] = [];
  if (!password) { errors.push('Password is required'); return { valid: false, errors }; }
  if (password.length < 8) errors.push('Password must be at least 8 characters');
  if (!/[A-Z]/.test(password)) errors.push('Password must contain uppercase letter');
  if (!/[a-z]/.test(password)) errors.push('Password must contain lowercase letter');
  if (!/[0-9]/.test(password)) errors.push('Password must contain a number');
  return { valid: errors.length === 0, errors };
}

export function validateAge(age: unknown): ValidationResult {
  const errors: string[] = [];
  if (age === null || age === undefined) { errors.push('Age is required'); return { valid: false, errors }; }
  const num = Number(age);
  if (isNaN(num)) errors.push('Age must be a number');
  else if (!Number.isInteger(num)) errors.push('Age must be a whole number');
  else if (num < 0 || num > 150) errors.push('Age must be between 0 and 150');
  return { valid: errors.length === 0, errors };
}

export function validateUrl(url: string): ValidationResult {
  const errors: string[] = [];
  if (!url) { errors.push('URL is required'); return { valid: false, errors }; }
  try {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      errors.push('URL must use http or https protocol');
    }
  } catch {
    errors.push('Invalid URL format');
  }
  return { valid: errors.length === 0, errors };
}
