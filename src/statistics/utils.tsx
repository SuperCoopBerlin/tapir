export function getFirstOfMonth(date: Date) {
  date.setDate(1);
  return date;
}

export function getLastOfMonth(date: Date) {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0);
}

export function getDateInputValue(date: Date) {
  if (isNaN(date.getTime())) {
    return undefined;
  }
  return date.toISOString().substring(0, 10);
}
