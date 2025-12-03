import React from "react";

interface SimpleMultiSelectProps {
  label: string;
  options: string[];
  selected: string[];
  onChange: (selected: string[]) => void;
  size?: number;
  disabled?: boolean;
}

export const SimpleMultiSelect: React.FC<SimpleMultiSelectProps> = ({
  label,
  options,
  selected,
  onChange,
  size = 5,
  disabled = false,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedOptions = Array.from(e.target.selectedOptions, opt => opt.value);
    onChange(selectedOptions);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {label && (
        <label style={{ fontWeight: 600, fontSize: '14px' }}>
          {label}:
        </label>
      )}
      <select
        multiple
        value={selected}
        onChange={handleChange}
        disabled={disabled}
        style={{
          width: '100%',
          minHeight: `${size * 24}px`,
          maxHeight: '300px',
          border: '1px solid #d1d5db',
          borderRadius: '6px',
          padding: '8px',
          fontSize: '14px',
          backgroundColor: disabled ? '#f3f4f6' : 'white',
        }}
      >
        {options.map(option => (
          <option 
            key={option} 
            value={option}
            style={{ 
              padding: '6px 12px',
              cursor: 'pointer',
            }}
          >
            {option}
          </option>
        ))}
      </select>
      <div style={{ fontSize: '0.8em', color: '#666' }}>
        {selected.length === 0 
          ? 'Nenhuma selecionada' 
          : selected.length === 1
          ? '1 variável selecionada'
          : `${selected.length} variáveis selecionadas`}
        {!disabled && ' • Use CTRL para seleção múltipla'}
      </div>
    </div>
  );
};