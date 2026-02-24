export function add(a: number, b: number): number {
  return a + b;
}

export function subtract(a: number, b: number): number {
  return a - b;
}

export function multiply(a: number, b: number): number {
  return a * b;
}

export function divide(a: number, b: number): number {
  if (b === 0) throw new Error('Division by zero');
  return a / b;
}

export function percentage(value: number, total: number): number {
  if (total === 0) throw new Error('Total cannot be zero');
  return (value / total) * 100;
}

export function average(numbers: number[]): number {
  if (numbers.length === 0) throw new Error('Cannot average empty array');
  return numbers.reduce((sum, n) => sum + n, 0) / numbers.length;
}
