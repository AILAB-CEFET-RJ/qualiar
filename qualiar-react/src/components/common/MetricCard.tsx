import React from "react";

interface MetricCardProps {
  value: string | number;
  label: string;
  subLabel?: string;
  icon?: string;
  color?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  value,
  label,
  subLabel,
  icon,
  color = '#f8f9fa'
}) => {
  return (
    <div style={{ 
      padding: 16, 
      backgroundColor: color, 
      borderRadius: 8, 
      textAlign: 'center' 
    }}>
      {icon && <div style={{ fontSize: '1.5em', marginBottom: 8 }}>{icon}</div>}
      <div style={{ fontSize: '2em', fontWeight: 'bold' }}>{value}</div>
      <div>{label}</div>
      {subLabel && (
        <div style={{ fontSize: '0.8em', color: '#666', marginTop: 4 }}>
          {subLabel}
        </div>
      )}
    </div>
  );
};