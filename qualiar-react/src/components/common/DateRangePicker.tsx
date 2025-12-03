import React from "react";

interface DateRangePickerProps {
  label: string;
  dateRange: [Date | null, Date | null];
  onChange: (range: [Date | null, Date | null]) => void;
  className?: string;
}

export const DateRangePicker: React.FC<DateRangePickerProps> = ({
  label,
  dateRange,
  onChange,
  className = "",
}) => {
  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = e.target.value ? new Date(e.target.value) : null;
    onChange([newDate, dateRange[1]]);
  };

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = e.target.value ? new Date(e.target.value) : null;
    onChange([dateRange[0], newDate]);
  };

  return (
    <div className={`date-range-picker ${className}`}>
      <label className="date-range-label">{label}:</label>
      <div className="date-inputs-container">
        <input
          type="date"
          value={dateRange[0]?.toISOString().slice(0, 10) || ''}
          onChange={handleStartDateChange}
          className="date-input"
        />
        <span className="date-range-separator">até</span>
        <input
          type="date"
          value={dateRange[1]?.toISOString().slice(0, 10) || ''}
          onChange={handleEndDateChange}
          className="date-input"
        />
      </div>
    </div>
  );
};