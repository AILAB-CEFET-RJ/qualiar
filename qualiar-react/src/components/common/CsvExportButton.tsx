// components/common/CsvExportButton.tsx
import React from 'react';
import Papa from 'papaparse';
import { DownloadIcon } from '../Icons';
import './CsvExportButton.css';

interface CsvExportButtonProps {
  data: any[];
  filename: string;
  label?: string;
  buttonText?: string;
  className?: string;
  iconSize?: number;
  iconColor?: string;
  // Função opcional para transformar os dados antes de exportar
  transformData?: (data: any[]) => any[];
  // Adicionar cabeçalho personalizado
  headers?: string[];
  // Configurações do PapaParse
  papaParseConfig?: Papa.UnparseConfig;
}

export const CsvExportButton: React.FC<CsvExportButtonProps> = ({
  data,
  filename,
  label = 'Exportar dados filtrados',
  buttonText = 'Baixar CSV filtrado',
  className = '',
  iconSize = 20,
  iconColor = '#4299e1',
  transformData,
  headers,
  papaParseConfig
}) => {
  const handleExport = () => {
    if (!data || data.length === 0) {
      alert('Nenhum dado disponível para exportar.');
      return;
    }

    try {
      // Aplica transformação personalizada se fornecida
      let dataToExport = transformData ? transformData(data) : data;
      
      // Configuração padrão do PapaParse
      const defaultConfig: Papa.UnparseConfig = {
        quotes: false,
        delimiter: ',',
        header: true,
        skipEmptyLines: true,
        ...papaParseConfig
      };

      // Adiciona cabeçalhos personalizados se fornecidos
      if (headers) {
        dataToExport = dataToExport.map(row => {
          const newRow: any = {};
          headers.forEach((header, index) => {
            const key = Object.keys(row)[index] || `col${index}`;
            newRow[header] = row[key];
          });
          return newRow;
        });
      }

      const csv = Papa.unparse(dataToExport, defaultConfig);
      
      // Cria e dispara o download
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      
      // Garante que o nome do arquivo tenha .csv
      const finalFilename = filename.endsWith('.csv') ? filename : `${filename}.csv`;
      
      link.href = url;
      link.download = finalFilename;
      link.style.display = 'none';
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error('Erro ao exportar CSV:', error);
      alert('Ocorreu um erro ao exportar os dados.');
    }
  };

  return (
    <div className={`csv-export-section ${className}`}>
      {label && (
        <h2 className="csv-export-title">
          <DownloadIcon size={iconSize} color={iconColor} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          {label}
        </h2>
      )}
      <button 
        onClick={handleExport}
        className="csv-export-button"
        disabled={!data || data.length === 0}
        title={data && data.length > 0 ? `Exportar ${data.length} registros` : 'Nenhum dado para exportar'}
      >
        <DownloadIcon size={16} style={{ marginRight: '8px' }} />
        {buttonText}
        {data && data.length > 0 && (
          <span className="csv-count-badge">({data.length})</span>
        )}
      </button>
      {data && data.length > 0 && (
        <div className="csv-info-text">
          Exportará {data.length.toLocaleString('pt-BR')} registros
        </div>
      )}
    </div>
  );
};

// Helper function para formatar datas (usada com transformData)
export const formatDateFields = (data: any[], dateFields: string[] = ['data_dia', 'DT_INTER', 'date']) => {
  return data.map(item => {
    const newItem = { ...item };
    dateFields.forEach(field => {
      if (newItem[field] instanceof Date) {
        newItem[field] = newItem[field].toISOString().slice(0, 10);
      } else if (typeof newItem[field] === 'string' && newItem[field]) {
        // Tenta converter string para data formatada
        try {
          const date = new Date(newItem[field]);
          if (!isNaN(date.getTime())) {
            newItem[field] = date.toISOString().slice(0, 10);
          }
        } catch (e) {
          // Mantém o valor original
        }
      }
    });
    return newItem;
  });
};

// Helper function para remover campos indesejados
export const filterFields = (data: any[], fieldsToKeep?: string[], fieldsToRemove?: string[]) => {
  return data.map(item => {
    const newItem: any = {};
    
    if (fieldsToKeep) {
      // Mantém apenas os campos especificados
      fieldsToKeep.forEach(field => {
        if (item[field] !== undefined) {
          newItem[field] = item[field];
        }
      });
    } else if (fieldsToRemove) {
      // Remove os campos especificados
      Object.keys(item).forEach(field => {
        if (!fieldsToRemove.includes(field)) {
          newItem[field] = item[field];
        }
      });
    } else {
      return item;
    }
    
    return newItem;
  });
};