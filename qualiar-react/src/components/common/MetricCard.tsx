import React from "react";
import "./MetricCard.css"; // Vamos criar este CSS

interface MetricCardProps {
  value: string | number;
  label: string;
  subLabel?: string;
  icon?: React.ReactNode | string; // Aceita ReactNode (seus ícones) ou string (emoji)
  color?: string;
  iconSize?: number;
  iconColor?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  value,
  label,
  subLabel,
  icon,
  color = '#f8f9fa',
  iconSize = 24,
  iconColor = '#4299e1'
}) => {
  // Função para renderizar o ícone corretamente
  const renderIcon = () => {
    if (!icon) return null;
    
    if (typeof icon === 'string') {
      // Se for string (emoji), renderiza como antes
      return <div className="metric-icon-emoji">{icon}</div>;
    } else {
      // Se for ReactNode (componente React Icon)
      return (
        <div className="metric-react-icon">
          {React.isValidElement(icon) 
            ? React.cloneElement(icon as React.ReactElement<any>, {
                size: iconSize,
                color: iconColor
              })
            : icon}
        </div>
      );
    }
  };

  return (
    <div className="metric-card" style={{ backgroundColor: color }}>
      {renderIcon()}
      <div className="metric-value">{value}</div>
      <div className="metric-label">{label}</div>
      {subLabel && (
        <div className="metric-sub-label">{subLabel}</div>
      )}
    </div>
  );
};