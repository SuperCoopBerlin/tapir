export function dateDifferenceInDays(a: Date, b: Date) {
  const milliseconds_per_day = 1000 * 60 * 60 * 24;
  return (a.getTime() - b.getTime()) / milliseconds_per_day;
}
