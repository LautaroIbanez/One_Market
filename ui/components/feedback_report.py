"""Feedback report component for Deep Dive tab.

This component shows performance metrics, rolling analysis,
and decision feedback in the UI.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.service.decision_tracker import get_tracker


def render_feedback_report():
    """Render the feedback report in the Deep Dive tab."""
    st.subheader("📊 Análisis de Retroalimentación")
    
    # Get tracker
    tracker = get_tracker()
    
    # Time period selector
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        days = st.selectbox(
            "Período de análisis",
            [7, 14, 30, 60, 90],
            index=2,  # Default to 30 days
            help="Número de días hacia atrás para analizar"
        )
    
    with col2:
        window = st.selectbox(
            "Ventana móvil",
            [3, 5, 7, 10, 14],
            index=2,  # Default to 7 days
            help="Ventana para métricas móviles"
        )
    
    with col3:
        st.info(f"📅 Analizando últimos {days} días con ventana de {window} días")
    
    st.markdown("---")
    
    # Performance metrics
    st.subheader("🎯 Métricas de Rendimiento")
    
    try:
        metrics = tracker.get_performance_metrics(days)
        
        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Decisiones Totales",
                metrics['total_decisions'],
                help="Total de decisiones tomadas en el período"
            )
        
        with col2:
            st.metric(
                "Tasa de Ejecución",
                f"{metrics['skip_rate']:.1%}",
                delta=f"{(1-metrics['skip_rate']):.1%} ejecutadas",
                help="Porcentaje de decisiones que se saltaron vs ejecutadas"
            )
        
        with col3:
            st.metric(
                "Tasa de Éxito",
                f"{metrics['win_rate']:.1%}",
                help="Porcentaje de trades ganadores"
            )
        
        with col4:
            st.metric(
                "P&L Total",
                f"${metrics['total_pnl']:,.2f}",
                delta=f"${metrics['avg_pnl']:,.2f} promedio",
                help="Ganancias/pérdidas totales y promedio"
            )
        
        # Additional metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Drawdown Máximo",
                f"{metrics['max_drawdown']:.1%}",
                help="Mayor pérdida desde un pico"
            )
        
        with col2:
            st.metric(
                "Ratio de Sharpe",
                f"{metrics['sharpe_ratio']:.2f}",
                help="Retorno ajustado por riesgo"
            )
        
        with col3:
            st.metric(
                "Confianza Promedio",
                f"{metrics['avg_confidence']:.1%}",
                help="Confianza promedio en las decisiones"
            )
        
        with col4:
            st.metric(
                "Decisiones Ejecutadas",
                metrics['executed_decisions'],
                help="Número de decisiones que se ejecutaron"
            )
        
    except Exception as e:
        st.error(f"Error al cargar métricas: {e}")
        return
    
    st.markdown("---")
    
    # Rolling analysis
    st.subheader("📈 Análisis de Tendencias")
    
    try:
        rolling_df = tracker.get_rolling_metrics(days, window)
        
        if not rolling_df.empty:
            # Create rolling charts
            fig = go.Figure()
            
            # Add P&L rolling
            fig.add_trace(go.Scatter(
                x=rolling_df['date'],
                y=rolling_df['rolling_pnl'],
                mode='lines',
                name='P&L Acumulado',
                line=dict(color='blue', width=2)
            ))
            
            fig.update_layout(
                title=f"P&L Acumulado ({window} días móviles)",
                xaxis_title="Fecha",
                yaxis_title="P&L ($)",
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Win rate and confidence
            fig2 = go.Figure()
            
            fig2.add_trace(go.Scatter(
                x=rolling_df['date'],
                y=rolling_df['rolling_win_rate'],
                mode='lines',
                name='Tasa de Éxito',
                yaxis='y',
                line=dict(color='green', width=2)
            ))
            
            fig2.add_trace(go.Scatter(
                x=rolling_df['date'],
                y=rolling_df['rolling_confidence'],
                mode='lines',
                name='Confianza Promedio',
                yaxis='y2',
                line=dict(color='orange', width=2)
            ))
            
            fig2.update_layout(
                title=f"Tasa de Éxito y Confianza ({window} días móviles)",
                xaxis_title="Fecha",
                yaxis=dict(title="Tasa de Éxito", side="left"),
                yaxis2=dict(title="Confianza", side="right", overlaying="y"),
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
        else:
            st.info("No hay datos suficientes para análisis de tendencias")
    
    except Exception as e:
        st.error(f"Error al generar análisis de tendencias: {e}")
    
    st.markdown("---")
    
    # Skip reasons analysis
    st.subheader("⏸️ Análisis de Decisiones Saltadas")
    
    try:
        skip_reasons = tracker.get_skip_reasons_summary(days)
        
        if skip_reasons:
            # Create pie chart
            reasons_df = pd.DataFrame([
                {'Razón': reason, 'Cantidad': count}
                for reason, count in skip_reasons.items()
            ])
            
            fig = px.pie(
                reasons_df,
                values='Cantidad',
                names='Razón',
                title="Distribución de Razones para Saltar"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Table
            st.subheader("Detalle de Razones")
            st.dataframe(reasons_df, use_container_width=True)
            
        else:
            st.info("No hay decisiones saltadas en el período analizado")
    
    except Exception as e:
        st.error(f"Error al analizar razones de skip: {e}")
    
    st.markdown("---")
    
    # Decision history
    st.subheader("📋 Historial de Decisiones")
    
    try:
        decisions = tracker.get_decision_history(days)
        outcomes = tracker.get_outcome_history(days)

        if decisions:
            # Convert decisions to DataFrame
            decisions_rows = []
            for d in decisions:
                decisions_rows.append({
                    'fecha': d.decision_date.date(),
                    'ejecutar': '✅' if d.should_execute else '⏸️',
                    'senal': '🟢 LONG' if d.signal == 1 else '🔴 SHORT' if d.signal == -1 else '⚪ FLAT',
                    'precio_entrada': d.entry_price,
                    'stop_loss': d.stop_loss,
                    'take_profit': d.take_profit,
                    'confianza': d.signal_strength if d.signal_strength is not None else None,
                    'razon_skip': d.skip_reason or None
                })
            decisions_df = pd.DataFrame(decisions_rows)

            # Convert outcomes to DataFrame
            outcome_rows = []
            for o in outcomes:
                outcome_rows.append({
                    'fecha': o.decision_date.date(),
                    'pnl': o.pnl,
                    'pnl_pct': o.pnl_pct,
                    'precio_ejecucion': o.execution_price,
                    'precio_salida': o.exit_price,
                    'motivo_cierre': o.exit_reason or (o.skip_reason if not o.was_executed else None)
                })
            outcomes_df = pd.DataFrame(outcome_rows) if outcome_rows else pd.DataFrame(columns=['fecha'])

            # Merge by date (si hay varias del mismo día, se agrupan por última ocurrencia)
            if not outcomes_df.empty:
                # En caso de múltiples outcomes por día, tomar el último
                outcomes_df = outcomes_df.sort_values('fecha').groupby('fecha').tail(1)
            merged = decisions_df.merge(outcomes_df, on='fecha', how='left')

            # Formatting columns safely
            def fmt_money(v):
                return f"${v:,.2f}" if pd.notna(v) else 'N/A'
            def fmt_pct(v):
                return f"{v:.2%}" if pd.notna(v) else 'N/A'
            def fmt_conf(v):
                return f"{v:.1%}" if pd.notna(v) else 'N/A'

            display_df = pd.DataFrame({
                'Fecha': merged['fecha'].astype(str),
                'Ejecutar': merged['ejecutar'],
                'Señal': merged['senal'],
                'Precio Entrada': merged['precio_entrada'].apply(fmt_money),
                'Stop Loss': merged['stop_loss'].apply(fmt_money),
                'Take Profit': merged['take_profit'].apply(fmt_money),
                'Confianza': merged['confianza'].apply(fmt_conf),
                'P&L ($)': merged['pnl'].apply(fmt_money),
                'P&L (%)': merged['pnl_pct'].apply(fmt_pct),
                'Ejecución': merged['precio_ejecucion'].apply(fmt_money),
                'Salida': merged['precio_salida'].apply(fmt_money),
                'Motivo Cierre': merged['motivo_cierre'].fillna('N/A'),
                'Razón Skip': merged['razon_skip'].fillna('N/A')
            })

            # Orden cronológico descendente
            display_df = display_df.sort_values('Fecha', ascending=False)
            st.dataframe(display_df, use_container_width=True)
            
        else:
            st.info("No hay decisiones en el período analizado")
    
    except Exception as e:
        st.error(f"Error al cargar historial de decisiones: {e}")
    
    st.markdown("---")
    
    # Recommendations
    st.subheader("💡 Recomendaciones")
    
    try:
        metrics = tracker.get_performance_metrics(days)
        
        recommendations = []
        
        # High skip rate
        if metrics['skip_rate'] > 0.7:
            recommendations.append(
                "🔍 **Tasa de skip alta**: Considera ajustar los filtros de volatilidad o riesgo para ejecutar más trades."
            )
        
        # Low win rate
        if metrics['win_rate'] < 0.4 and metrics['executed_decisions'] > 5:
            recommendations.append(
                "📉 **Tasa de éxito baja**: Revisa los parámetros de entrada, stop loss y take profit."
            )
        
        # High drawdown
        if metrics['max_drawdown'] < -0.1:  # More than 10% drawdown
            recommendations.append(
                "⚠️ **Drawdown alto**: Considera reducir el tamaño de posición o ajustar el riesgo por trade."
            )
        
        # Low confidence
        if metrics['avg_confidence'] < 0.6:
            recommendations.append(
                "🤔 **Confianza baja**: Revisa la calidad de las señales y considera mejorar los filtros."
            )
        
        # Good performance
        if metrics['win_rate'] > 0.6 and metrics['total_pnl'] > 0:
            recommendations.append(
                "🎉 **Rendimiento excelente**: Mantén los parámetros actuales y considera aumentar el tamaño de posición gradualmente."
            )
        
        if recommendations:
            for rec in recommendations:
                st.markdown(rec)
        else:
            st.info("✅ No hay recomendaciones específicas en este momento.")
    
    except Exception as e:
        st.error(f"Error al generar recomendaciones: {e}")

