export function formatDate(
  date: Date | undefined | null,
  includeTime = true,
): string {
  if (!date) {
    return "";
  }

  const options: Intl.DateTimeFormatOptions = {
    year: "2-digit",
    month: "2-digit",
    day: "2-digit",
  };
  if (includeTime) {
    options.hour = "2-digit";
    options.minute = "2-digit";
  }

  return date.toLocaleDateString("de-DE", options);
}
