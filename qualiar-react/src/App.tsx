import { Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import EstacoesPage from "./pages/EstacoesPage";
import AnaliseRio from "./pages/AnaliseRio";
import DadosSaude from "./pages/DadosSaude";
import PoluentesDoencas from "./pages/PoluentesDoencas";
import type { JSX } from "react";

export default function App(): JSX.Element {
  return (
    <div className="app-root">
      <Sidebar />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Navigate to="/estacoes" replace />} />
          <Route path="/estacoes" element={<EstacoesPage />} />
          <Route path="/rio" element={<AnaliseRio />} />
          <Route path="/saude" element={<DadosSaude />} />
          <Route path="/poluentes" element={<PoluentesDoencas />} />
          <Route path="*" element={<div style={{ padding: 24 }}>Página não encontrada</div>} />
        </Routes>
      </main>
    </div>
  );
}
