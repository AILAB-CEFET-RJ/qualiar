import "./LoadingState.css";

export function LoadingState({ message = "Carregando..." }: { message?: string }) {
  return (
    <div className="loading-state-rio">
      <div className="spinner-rio" />
      {message}
    </div>
  );
}
