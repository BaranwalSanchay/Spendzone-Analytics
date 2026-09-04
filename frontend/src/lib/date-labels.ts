const MONTH_INDEX: Record<string, number> = {
  jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5,
  jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11,
};

/**
 * Parses the loosely-formatted month labels used across the dashboard's JSON
 * data ("Jul 2023", "Jul'23", "July'23", "2023-07") into a real Date anchored
 * to the 1st of that month, for date-range filtering. Returns null if the
 * label doesn't match any known shape.
 */
export function parseMonthLabel(label: string | undefined | null): Date | null {
  if (!label) return null;

  // ISO "YYYY-MM"
  const isoMatch = label.match(/^(\d{4})-(\d{2})$/);
  if (isoMatch) {
    return new Date(Number(isoMatch[1]), Number(isoMatch[2]) - 1, 1);
  }

  // "MonthName'YY", "MonthName YYYY", etc. (e.g. "Jul'23", "July'23", "Jul 2023")
  const nameMatch = label.match(/^([A-Za-z]+)['\s]?(\d{2,4})$/);
  if (nameMatch) {
    const monthIndex = MONTH_INDEX[nameMatch[1].slice(0, 3).toLowerCase()];
    if (monthIndex === undefined) return null;
    let year = Number(nameMatch[2]);
    if (year < 100) year += 2000;
    return new Date(year, monthIndex, 1);
  }

  const fallback = new Date(label);
  return Number.isNaN(fallback.getTime()) ? null : fallback;
}

/** True if the parsed month label falls within [from, to] (inclusive, to optional). */
export function isMonthLabelInRange(
  label: string | undefined | null,
  from: Date | undefined,
  to: Date | undefined
): boolean {
  if (!from) return true;
  const date = parseMonthLabel(label);
  if (!date) return true; // don't hide rows we can't parse
  if (date < from) return false;
  if (to && date > to) return false;
  return true;
}
