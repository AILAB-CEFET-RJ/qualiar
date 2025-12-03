import React, { useState, useEffect, useRef } from "react";

interface MultiSelectProps {
  label: string;
  options: string[];
  selected: string[];
  onChange: (selected: string[]) => void;
  size?: number;
  withAllOption?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export const MultiSelect: React.FC<MultiSelectProps> = ({
  label,
  options,
  selected,
  onChange,
  size = 5,
  withAllOption = true,
  className = "",
  style = {},
}) => {
  const [internalSelected, setInternalSelected] = useState<string[]>(selected);
  const [isAllSelected, setIsAllSelected] = useState(false);
  const selectRef = useRef<HTMLSelectElement>(null);

  // Sincronizar com props externas
  useEffect(() => {
    setInternalSelected(selected);
    setIsAllSelected(selected.length === options.length || selected.length === 0);
  }, [selected, options.length]);

  const allOptions = withAllOption ? ['Todos', ...options] : options;

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedOptions = Array.from(e.target.selectedOptions, opt => opt.value);
    
    // Se "Todos" foi selecionado ou desselecionado
    if (withAllOption) {
      const wasAllSelected = isAllSelected;
      const nowAllSelected = selectedOptions.includes('Todos');
      
      if (nowAllSelected && !wasAllSelected) {
        // Selecionar todos os itens reais
        onChange([...options]);
        return;
      } else if (wasAllSelected && !nowAllSelected && selectedOptions.length > 0) {
        // Desselecionar "Todos" mas manter outras seleções
        const realSelections = selectedOptions.filter(opt => opt !== 'Todos');
        onChange(realSelections);
        return;
      } else if (selectedOptions.length === 0) {
        // Nada selecionado
        onChange([]);
        return;
      }
    }
    
    // Filtrar "Todos" das seleções reais
    const realSelections = withAllOption 
      ? selectedOptions.filter(opt => opt !== 'Todos')
      : selectedOptions;
    
    onChange(realSelections);
  };

  // Determinar qual valor mostrar no select
  const getSelectValue = () => {
    if (withAllOption) {
      if (isAllSelected || selected.length === 0) {
        return ['Todos'];
      }
    }
    return selected;
  };

  return (
    <div className={`multi-select-container ${className}`} style={style}>
      {label && <label className="multi-select-label">{label}:</label>}
      <select
        ref={selectRef}
        multiple
        value={getSelectValue()}
        onChange={handleChange}
        className="multi-select"
        size={Math.min(size, Math.max(3, allOptions.length))}
        style={{ width: '100%', minHeight: '100px' }}
      >
        {allOptions.map(option => (
          <option 
            key={option} 
            value={option}
            style={{ padding: '4px 8px' }}
          >
            {option}
          </option>
        ))}
      </select>
      <div className="multi-select-hint" style={{ fontSize: '0.8em', color: '#666', marginTop: '4px' }}>
        {selected.length === 0 
          ? 'Nenhuma selecionada' 
          : selected.length === options.length
          ? 'Todas selecionadas'
          : `${selected.length} selecionada(s)`}
      </div>
    </div>
  );
};

// Estilos opcionais que você pode adicionar ao seu CSS
export const multiSelectStyles = `
  .multi-select-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .multi-select-label {
    font-weight: 600;
    font-size: 14px;
  }
  
  .multi-select {
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 4px;
    background-color: white;
    font-size: 14px;
  }
  
  .multi-select:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
  
  .multi-select option {
    padding: 8px 12px;
    cursor: pointer;
  }
  
  .multi-select option:hover {
    background-color: #f3f4f6;
  }
  
  .multi-select option:checked {
    background-color: #3b82f6;
    color: white;
  }
`;