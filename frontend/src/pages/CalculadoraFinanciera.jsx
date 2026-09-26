import React, { useState } from 'react';
import api from '../services/api';

function CalculadoraFinanciera() {
  const [monto, setMonto] = useState('');
  const [tasa, setTasa] = useState('');
  const [plazo, setPlazo] = useState('');
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState('');

  const handleCalcular = async (e) => {
    e.preventDefault();
    try {
      // Ajusta la ruta '/calcular-frances' según el endpoint que ya tengas en tu FastAPI
      const response = await api.post('/calcular-frances', {
        monto: parseFloat(monto),
        tasa: parseFloat(tasa),
        plazo: parseInt(plazo)
      });
      setResultado(response.data);
      setError('');
    } catch (err) {
      setError('Error al conectar con el backend para el cálculo financiero.');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h3>Simulador de Crédito - Método Francés</h3>
      <form onSubmit={handleCalcular} style={{ maxWidth: '400px', marginBottom: '25px' }}>
        <div style={{ marginBottom: '12px' }}>
          <label>Monto del Préstamo:</label><br />
          <input 
            type="number" 
            value={monto} 
            onChange={(e) => setMonto(e.target.value)} 
            required 
            style={{ width: '100%', padding: '8px', marginTop: '4px' }}
          />
        </div>
        <div style={{ marginBottom: '12px' }}>
          <label>Tasa de Interés (%):</label><br />
          <input 
            type="number" 
            step="0.0000001" 
            value={tasa} 
            onChange={(e) => setTasa(e.target.value)} 
            required 
            style={{ width: '100%', padding: '8px', marginTop: '4px' }}
          />
        </div>
        <div style={{ marginBottom: '12px' }}>
          <label>Plazo (Meses):</label><br />
          <input 
            type="number" 
            value={plazo} 
            onChange={(e) => setPlazo(e.target.value)} 
            required 
            style={{ width: '100%', padding: '8px', marginTop: '4px' }}
          />
        </div>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" style={{ width: '100%', padding: '10px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px' }}>
          Calcular Cronograma
        </button>
      </form>

      {resultado && (
        <div>
          <h4>Resultado del Cronograma de Pagos</h4>
          <table border="1" cellPadding="8" style={{ borderCollapse: 'collapse', width: '100%', marginTop: '10px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f2f2f2' }}>
                <th>N° Cuota</th>
                <th>Cuota Fija</th>
                <th>Interés</th>
                <th>Amortización</th>
                <th>Saldo Pendiente</th>
              </tr>
            </thead>
            <tbody>
              {resultado.cuotas?.map((item, index) => (
                <tr key={index}>
                  <td>{item.nro}</td>
                  <td>{item.cuota}</td>
                  <td>{item.interes}</td>
                  <td>{item.amortizacion}</td>
                  <td>{item.saldo}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default CalculadoraFinanciera;