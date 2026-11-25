import React from 'react';
import CalculadoraFinanciera from './CalculadoraFinanciera';

function Dashboard({ onLogout }) {
  return (
    <div style={{ padding: '30px' }}>
      <nav style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #ddd', paddingBottom: '15px' }}>
        <h2>TBF Finanzas e Ingeniería Económica - Sistema</h2>
        <button onClick={onLogout} style={{ padding: '8px 15px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px' }}>
          Cerrar Sesión
        </button>
      </nav>
      
      <CalculadoraFinanciera />
    </div>
  );
}

export default Dashboard;