// components/ChartViewer.tsx (ou adicione no topo de DadosSaude.tsx)
import { useState, useRef } from "react";
import { DownloadIcon } from "./Icons";
import "./ChartViewer.css"

interface ChartViewerProps {
  url: string;
  title?: string;
  onDownload: () => void;
}

export const ChartViewer = ({ url, title, onDownload }: ChartViewerProps) => {
  const [zoom, setZoom] = useState(1);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.5, 4)); // Max 4x
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.5, 1)); // Min 1x
  const handleReset = () => setZoom(1);

  return (
    <div className="chart-viewer-card">
      {/* Barra de Ferramentas */}
      <div className="chart-toolbar">
        {title && <span className="chart-label">{title}</span>}
        
        <div className="chart-controls">
          <div className="zoom-group">
            <button onClick={handleZoomOut} disabled={zoom === 1} title="Diminuir Zoom">
              -
            </button>
            <span className="zoom-indicator">{(zoom * 100).toFixed(0)}%</span>
            <button onClick={handleZoomIn} disabled={zoom === 4} title="Aumentar Zoom">
              +
            </button>
            <button onClick={handleReset} className="reset-btn" title="Resetar">
              ↺
            </button>
          </div>
          
          <button onClick={onDownload} className="download-action-btn" title="Baixar SVG">
            <DownloadIcon style={{ marginRight: 4 }} /> SVG
          </button>
        </div>
      </div>

      {/* Área de Visualização com Scroll */}
      <div 
        className="chart-viewport" 
        ref={containerRef}
      >
        <div 
          className="chart-content"
          style={{ 
            transform: `scale(${zoom})`,
            transformOrigin: "top left",
            // Ajusta a largura baseada no zoom para permitir scroll horizontal/vertical
            width: zoom === 1 ? "100%" : `${zoom * 100}%`,
            height: zoom === 1 ? "auto" : "auto" 
          }}
        >
          <object
            data={url}
            type="image/svg+xml"
            className="chart-object"
            style={{ pointerEvents: zoom > 1 ? "none" : "auto" }} // Melhora a rolagem quando com zoom
          />
        </div>
      </div>
    </div>
  );
};