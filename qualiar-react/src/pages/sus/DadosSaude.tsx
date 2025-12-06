// pages/sus/DadosSaude.tsx
import { useState, useEffect } from "react";
import { MetricCard } from "../../components/common/MetricCard";
import {
  StatsIcon,
  HospitalIcon,
  PessoaIcon,
  WarningIcon,
  ClockIcon,
  CalendarIcon
} from "../../components/Icons";
import "./DadosSaude.css";
import {ChartViewer} from "../../components/ChartViewer";
import { LoadingState } from "../../components/common/LoadingState";

interface StaticChartData {
  generated_at: string;
  metrics: {
    total_internacoes: number;
    media_idade: number;
    taxa_mortalidade: number;
    media_permanencia: number;
    ano_min: number;
    ano_max: number;
  };
  charts: Record<string, string>;
}

export default function DadosSaudeAvancado() {
  const [staticData, setStaticData] = useState<StaticChartData | null>(null);
  const [staticLoading, setStaticLoading] = useState(true);
  const [staticError, setStaticError] = useState<string | null>(null);

  useEffect(() => {
    const loadStaticData = async () => {
      try {
        const response = await fetch("/charts/metadata.json");
        if (!response.ok) throw new Error("Gráficos estáticos não encontrados");
        const data = await response.json();
        setStaticData(data);
        setStaticError(null);
      } catch (err) {
        setStaticError("Gráficos estáticos em geração. Aguarde ou execute a geração.");
      } finally {
        setStaticLoading(false);
      }
    };

    loadStaticData();
  }, []);

  const getStaticChartUrl = (chartName: string) => `/charts/${chartName}`;

  const handleDownload = (chartName: string) => {
    const link = document.createElement("a");
    link.href = `/charts/${chartName}`;
    link.download = chartName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (staticLoading) return <LoadingState message="Carregando dados..." />;

  if (!staticData)
    return (
      <div className="error-state">
        Erro ao carregar dados. Verifique a geração dos gráficos.
      </div>
    );

  const metrics = staticData.metrics;

  return (
    <div className="dados-saude-container">
      <h1 className="dados-saude-title">
        <HospitalIcon style={{ marginRight: "8px", verticalAlign: "middle" }} />
        SIH/SUS — Internações Respiratórias
        <span style={{ fontSize: "0.8em", color: "#666", marginLeft: "10px" }}>
          ({metrics.ano_min} - {metrics.ano_max})
        </span>
      </h1>

      {staticError && (
        <div className="warning-banner">
          <WarningIcon style={{ marginRight: "8px" }} /> {staticError}
          <a href="/api/generate-charts" style={{ marginLeft: "10px" }}>
            Gerar gráficos
          </a>
        </div>
      )}

      {/* MÉTRICAS */}
      <div className="section">
        <h2 className="section-title">
          <StatsIcon style={{ marginRight: "8px", verticalAlign: "middle" }} />
          Visão Geral
          <span style={{ fontSize: "0.7em", marginLeft: "10px", color: "#666" }}>
            Base: {metrics.total_internacoes.toLocaleString("pt-BR")} registros
          </span>
        </h2>

        <div className="metricas-grid">
          <MetricCard
            value={metrics.total_internacoes.toLocaleString("pt-BR")}
            label="Total de Internações"
            icon={<HospitalIcon size={30} color="#3182ce" />}
            subLabel="Contagem total"
          />

          <MetricCard
            value={metrics.media_idade.toFixed(1)}
            label="Idade Média"
            icon={<PessoaIcon size={30} color="#38a169" />}
            subLabel="Em anos"
          />

          <MetricCard
            value={`${metrics.taxa_mortalidade.toFixed(2)}%`}
            label="Taxa de Mortalidade"
            icon={<WarningIcon size={30} color="#e53e3e" />}
            subLabel="Porcentagem"
          />

          <MetricCard
            value={metrics.media_permanencia.toFixed(1)}
            label="Permanência Média"
            icon={<ClockIcon size={30} color="#d69e2e" />}
            subLabel="Em dias"
          />
        </div>
      </div>

{/* GRÁFICOS COM ZOOM */}
      
      <div className="section">
        <h2 className="section-title">
          <StatsIcon style={{ marginRight: "8px" }} /> Série Temporal
        </h2>
        <ChartViewer 
          url={getStaticChartUrl("time_series.svg")}
          title="Evolução Temporal das Internações"
          onDownload={() => handleDownload("time_series.svg")}
        />
      </div>

      <div className="section">
        <h2 className="section-title">
          <CalendarIcon style={{ marginRight: "8px" }} /> Sazonalidade
        </h2>
        <div className="heatmaps-grid">
          <ChartViewer 
            url={getStaticChartUrl("heatmap_count.svg")}
            title="Mapa de Calor: Frequência Absoluta"
            onDownload={() => handleDownload("heatmap_count.svg")}
          />
          <ChartViewer 
            url={getStaticChartUrl("heatmap_share.svg")}
            title="Mapa de Calor: Intensidade Relativa"
            onDownload={() => handleDownload("heatmap_share.svg")}
          />
        </div>
      </div>

      <div className="section">
        <h2 className="section-title">
          <PessoaIcon style={{ marginRight: "8px" }} /> Distribuição Demográfica
        </h2>
        <div className="distribution-grid">
          <ChartViewer 
            url={getStaticChartUrl("sex_distribution_pie.svg")}
            title="Distribuição por Sexo (Pizza)"
            onDownload={() => handleDownload("sex_distribution_pie.svg")}
          />
          <ChartViewer 
            url={getStaticChartUrl("sex_distribution_bar.svg")}
            title="Comparativo por Sexo (Barras)"
            onDownload={() => handleDownload("sex_distribution_bar.svg")}
          />
        </div>
      </div>

      <div className="section">
        <h2 className="section-title">
          <PessoaIcon style={{ marginRight: "8px" }} /> Distribuição Etária
        </h2>
        <ChartViewer 
            url={getStaticChartUrl("age_distribution.svg")}
            title="Histograma de Idades"
            onDownload={() => handleDownload("age_distribution.svg")}
        />
      </div>

      <div className="section">
        <h2 className="section-title">
          <HospitalIcon style={{ marginRight: "8px" }} /> Grupos CID-10
        </h2>
        <ChartViewer 
            url={getStaticChartUrl("cid_distribution.svg")}
            title="Principais Diagnósticos"
            onDownload={() => handleDownload("cid_distribution.svg")}
        />
      </div>

      <div className="section">
        <h2 className="section-title">
          <WarningIcon style={{ marginRight: "8px" }} /> Mortalidade no Tempo
        </h2>
        <ChartViewer 
            url={getStaticChartUrl("mortality_time_series.svg")}
            title="Taxa de Mortalidade (% no período)"
            onDownload={() => handleDownload("mortality_time_series.svg")}
        />
      </div>

      <div className="footer">
        Versão Otimizada • Dados SIH/SUS • Rio de Janeiro
        <div style={{ fontSize: "0.9em", color: "#666", marginTop: "5px" }}>
          Gráficos gerados em {new Date(staticData.generated_at).toLocaleDateString("pt-BR")}
        </div>
      </div>
    </div>
  );
}
