import { type JSX } from "react";
import { NavLink } from "react-router-dom";
import "./Sidebar.css";

/**
 * Coloque um ícone PNG em src/assets/icon.png
 * Recomendo 64x64 ou 48x48 — o arquivo será usado aqui.
 */

export default function Sidebar(): JSX.Element {
  return (
    <nav className="sidebar">
      <div className="sidebar-top">
        <img src="/src/assets/icon.png" alt="icon" className="sidebar-icon" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
        <h1 className="sidebar-title">QualiAR</h1>
      </div>

      <div className="sidebar-links">
        <NavLink to="/rio" className={({isActive}) => isActive ? "link active" : "link"}>Qualidade do ar — Rio</NavLink>
        <NavLink to="/saude" className={({isActive}) => isActive ? "link active" : "link"}>Dados de Saúde</NavLink>
        <NavLink to="/estacoes" className={({isActive}) => isActive ? "link active" : "link"}>Estações (EDA)</NavLink>
        <NavLink to="/poluentes" className={({isActive}) => isActive ? "link active" : "link"}>Poluentes x Doenças</NavLink>
      </div>

      <div className="sidebar-footer">
        <small>Versão local</small>
      </div>
    </nav>
  );
}
