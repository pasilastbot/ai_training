interface RawRecord {
  id: string;
  first_name: string;
  last_name: string;
  email_address: string;
  date_of_birth: string;
  account_balance: string;
}

interface ProcessedRecord {
  id: string;
  fullName: string;
  email: string;
  age: number;
  balance: number;
  tier: 'bronze' | 'silver' | 'gold' | 'platinum';
}

export function transformRecord(raw: RawRecord): ProcessedRecord {
  const age = calculateAge(raw.date_of_birth);
  const balance = parseFloat(raw.account_balance);
  return {
    id: raw.id,
    fullName: `${raw.first_name} ${raw.last_name}`.trim(),
    email: raw.email_address.toLowerCase(),
    age,
    balance,
    tier: determineTier(balance),
  };
}

export function calculateAge(dateOfBirth: string): number {
  const birth = new Date(dateOfBirth);
  const now = new Date();
  let age = now.getFullYear() - birth.getFullYear();
  const monthDiff = now.getMonth() - birth.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && now.getDate() < birth.getDate())) {
    age--;
  }
  return age;
}

export function determineTier(balance: number): 'bronze' | 'silver' | 'gold' | 'platinum' {
  if (balance >= 100000) return 'platinum';
  if (balance >= 50000) return 'gold';
  if (balance >= 10000) return 'silver';
  return 'bronze';
}

export function transformBatch(records: RawRecord[]): {
  processed: ProcessedRecord[];
  errors: { index: number; error: string }[];
} {
  const processed: ProcessedRecord[] = [];
  const errors: { index: number; error: string }[] = [];

  records.forEach((record, index) => {
    try {
      processed.push(transformRecord(record));
    } catch (err) {
      errors.push({ index, error: (err as Error).message });
    }
  });

  return { processed, errors };
}

export function groupByTier(records: ProcessedRecord[]): Record<string, ProcessedRecord[]> {
  return records.reduce((groups, record) => {
    const tier = record.tier;
    if (!groups[tier]) groups[tier] = [];
    groups[tier].push(record);
    return groups;
  }, {} as Record<string, ProcessedRecord[]>);
}
