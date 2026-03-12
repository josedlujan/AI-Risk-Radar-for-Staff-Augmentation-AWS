"""MockDataGenerator for creating realistic team signals and risk scenarios."""

import random
from datetime import datetime, timezone
from typing import Dict, List, Literal
from models.team_signal import TeamSignal, SignalMetadata
from models.risk_record import RiskRecord, SeverityLevel


ScenarioType = Literal["healthy", "overloaded", "knowledge_silo", "dependency_heavy", "attrition_warning"]


class MockDataGenerator:
    """Generates realistic mock data for team risk analysis demonstrations."""
    
    def __init__(self, seed: int = None):
        """Initialize generator with optional seed for reproducibility."""
        if seed is not None:
            random.seed(seed)
    
    def generate_team_signals(
        self,
        team_size: int = 8,
        project_count: int = 3,
        team_id: str = "demo-team-001"
    ) -> Dict[str, float]:
        """
        Generate realistic signal values with controlled variance.
        
        Args:
            team_size: Number of engineers in the team (default: 8)
            project_count: Number of projects (default: 3)
            team_id: Team identifier
            
        Returns:
            Dictionary with five risk dimension values (0-100)
        """
        # Base values with realistic variance
        # Higher values = higher risk
        base_delivery = 45 + random.uniform(-15, 15)
        base_knowledge = 55 + random.uniform(-20, 20)
        base_dependency = 40 + random.uniform(-15, 15)
        base_workload = 50 + random.uniform(-20, 20)
        base_attrition = 35 + random.uniform(-15, 15)
        
        # Adjust based on team characteristics
        if team_size < 5:
            # Small teams have higher knowledge concentration risk
            base_knowledge += 15
            base_attrition += 10
        
        if project_count > team_size / 2:
            # Too many projects per person increases workload and dependency risk
            base_workload += 20
            base_dependency += 15
            base_delivery += 10
        
        return {
            "delivery_cadence": self._clamp(base_delivery),
            "knowledge_concentration": self._clamp(base_knowledge),
            "dependency_risk": self._clamp(base_dependency),
            "workload_distribution": self._clamp(base_workload),
            "attrition_signal": self._clamp(base_attrition)
        }
    
    def generate_risk_scenario(
        self,
        scenario: ScenarioType,
        team_id: str = "demo-team-001",
        team_size: int = 8,
        project_count: int = 3
    ) -> Dict[str, any]:
        """
        Generate predefined risk scenarios with corresponding signals and risks.
        
        Args:
            scenario: Type of scenario to generate
            team_id: Team identifier
            team_size: Number of engineers
            project_count: Number of projects
            
        Returns:
            Dictionary containing team_signal, risks, and metadata
        """
        timestamp = datetime.now(timezone.utc)
        
        if scenario == "healthy":
            signals = {
                "delivery_cadence": 25.0,
                "knowledge_concentration": 30.0,
                "dependency_risk": 20.0,
                "workload_distribution": 28.0,
                "attrition_signal": 15.0
            }
            risks = self._generate_healthy_risks(team_id, signals, timestamp)
            
        elif scenario == "overloaded":
            signals = {
                "delivery_cadence": 75.0,
                "knowledge_concentration": 55.0,
                "dependency_risk": 60.0,
                "workload_distribution": 85.0,
                "attrition_signal": 70.0
            }
            risks = self._generate_overloaded_risks(team_id, signals, timestamp)
            
        elif scenario == "knowledge_silo":
            signals = {
                "delivery_cadence": 45.0,
                "knowledge_concentration": 88.0,
                "dependency_risk": 50.0,
                "workload_distribution": 55.0,
                "attrition_signal": 40.0
            }
            risks = self._generate_knowledge_silo_risks(team_id, signals, timestamp)
            
        elif scenario == "dependency_heavy":
            signals = {
                "delivery_cadence": 65.0,
                "knowledge_concentration": 50.0,
                "dependency_risk": 82.0,
                "workload_distribution": 60.0,
                "attrition_signal": 45.0
            }
            risks = self._generate_dependency_risks(team_id, signals, timestamp)
            
        elif scenario == "attrition_warning":
            signals = {
                "delivery_cadence": 55.0,
                "knowledge_concentration": 60.0,
                "dependency_risk": 48.0,
                "workload_distribution": 70.0,
                "attrition_signal": 90.0
            }
            risks = self._generate_attrition_risks(team_id, signals, timestamp)
        
        else:
            raise ValueError(f"Unknown scenario: {scenario}")
        
        # Create TeamSignal object
        team_signal = TeamSignal(
            team_id=team_id,
            timestamp=timestamp,
            delivery_cadence=signals["delivery_cadence"],
            knowledge_concentration=signals["knowledge_concentration"],
            dependency_risk=signals["dependency_risk"],
            workload_distribution=signals["workload_distribution"],
            attrition_signal=signals["attrition_signal"],
            metadata=SignalMetadata(
                team_size=team_size,
                project_count=project_count,
                aggregation_period="weekly"
            )
        )
        
        return {
            "team_signal": team_signal,
            "risks": risks,
            "scenario": scenario,
            "is_mock": True
        }
    
    def _generate_healthy_risks(
        self,
        team_id: str,
        signals: Dict[str, float],
        timestamp: datetime
    ) -> List[RiskRecord]:
        """Generate risks for healthy team scenario (one risk per severity)."""
        analysis_id = f"analysis-{timestamp.strftime('%Y%m%d%H%M%S')}"
        
        return [
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="delivery_cadence",
                severity=SeverityLevel.LOW,
                detected_at=timestamp,
                description_en="Delivery cadence is stable with minor variations",
                description_es="La cadencia de entrega es estable con variaciones menores",
                recommendations_en=["Continue monitoring sprint velocity", "Maintain current practices"],
                recommendations_es=["Continuar monitoreando la velocidad del sprint", "Mantener las prácticas actuales"],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="knowledge_concentration",
                severity=SeverityLevel.MEDIUM,
                detected_at=timestamp,
                description_en="Some knowledge concentration detected in specific areas",
                description_es="Se detectó cierta concentración de conocimiento en áreas específicas",
                recommendations_en=["Implement pair programming sessions", "Document critical processes"],
                recommendations_es=["Implementar sesiones de programación en pareja", "Documentar procesos críticos"],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="workload_distribution",
                severity=SeverityLevel.HIGH,
                detected_at=timestamp,
                description_en="Workload shows some imbalance across team members",
                description_es="La carga de trabajo muestra cierto desequilibrio entre los miembros del equipo",
                recommendations_en=["Review task allocation in next planning", "Consider workload rebalancing"],
                recommendations_es=["Revisar la asignación de tareas en la próxima planificación", "Considerar reequilibrar la carga de trabajo"],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="attrition_signal",
                severity=SeverityLevel.CRITICAL,
                detected_at=timestamp,
                description_en="Critical attrition indicators detected requiring immediate attention",
                description_es="Se detectaron indicadores críticos de desgaste que requieren atención inmediata",
                recommendations_en=["Schedule one-on-one meetings with team members", "Review compensation and growth opportunities", "Assess team morale and work-life balance"],
                recommendations_es=["Programar reuniones individuales con los miembros del equipo", "Revisar compensación y oportunidades de crecimiento", "Evaluar la moral del equipo y el equilibrio trabajo-vida"],
                signal_values=signals
            )
        ]

    
    def _generate_overloaded_risks(
        self,
        team_id: str,
        signals: Dict[str, float],
        timestamp: datetime
    ) -> List[RiskRecord]:
        """Generate risks for overloaded team scenario."""
        analysis_id = f"analysis-{timestamp.strftime('%Y%m%d%H%M%S')}"
        
        return [
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="workload_distribution",
                severity=SeverityLevel.CRITICAL,
                detected_at=timestamp,
                description_en="Severe workload imbalance detected with team members significantly overloaded",
                description_es="Se detectó un desequilibrio severo de carga de trabajo con miembros del equipo significativamente sobrecargados",
                recommendations_en=[
                    "Immediately redistribute tasks to balance workload",
                    "Consider bringing in additional resources",
                    "Postpone non-critical features",
                    "Review and adjust sprint commitments"
                ],
                recommendations_es=[
                    "Redistribuir inmediatamente las tareas para equilibrar la carga de trabajo",
                    "Considerar traer recursos adicionales",
                    "Posponer características no críticas",
                    "Revisar y ajustar los compromisos del sprint"
                ],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="delivery_cadence",
                severity=SeverityLevel.HIGH,
                detected_at=timestamp,
                description_en="Delivery velocity declining due to excessive workload",
                description_es="La velocidad de entrega está disminuyendo debido a la carga de trabajo excesiva",
                recommendations_en=[
                    "Reduce scope of current sprint",
                    "Focus on completing in-progress work",
                    "Limit work-in-progress items"
                ],
                recommendations_es=[
                    "Reducir el alcance del sprint actual",
                    "Enfocarse en completar el trabajo en progreso",
                    "Limitar los elementos de trabajo en progreso"
                ],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="attrition_signal",
                severity=SeverityLevel.HIGH,
                detected_at=timestamp,
                description_en="High attrition risk due to sustained overwork",
                description_es="Alto riesgo de desgaste debido al exceso de trabajo sostenido",
                recommendations_en=[
                    "Address burnout concerns immediately",
                    "Ensure team takes time off",
                    "Review workload expectations with leadership"
                ],
                recommendations_es=[
                    "Abordar las preocupaciones de agotamiento inmediatamente",
                    "Asegurar que el equipo tome tiempo libre",
                    "Revisar las expectativas de carga de trabajo con el liderazgo"
                ],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="dependency_risk",
                severity=SeverityLevel.MEDIUM,
                detected_at=timestamp,
                description_en="Dependencies causing delays in overloaded environment",
                description_es="Las dependencias están causando retrasos en un entorno sobrecargado",
                recommendations_en=[
                    "Identify and resolve blocking dependencies",
                    "Improve cross-team communication"
                ],
                recommendations_es=[
                    "Identificar y resolver dependencias bloqueantes",
                    "Mejorar la comunicación entre equipos"
                ],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="knowledge_concentration",
                severity=SeverityLevel.LOW,
                detected_at=timestamp,
                description_en="Knowledge distribution is adequate despite high workload",
                description_es="La distribución del conocimiento es adecuada a pesar de la alta carga de trabajo",
                recommendations_en=["Continue knowledge sharing practices"],
                recommendations_es=["Continuar las prácticas de intercambio de conocimientos"],
                signal_values=signals
            )
        ]
    
    def _generate_knowledge_silo_risks(
        self,
        team_id: str,
        signals: Dict[str, float],
        timestamp: datetime
    ) -> List[RiskRecord]:
        """Generate risks for knowledge silo scenario."""
        analysis_id = f"analysis-{timestamp.strftime('%Y%m%d%H%M%S')}"
        
        return [
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="knowledge_concentration",
                severity=SeverityLevel.CRITICAL,
                detected_at=timestamp,
                description_en="Critical knowledge concentration - key expertise held by very few team members",
                description_es="Concentración crítica de conocimiento - la experiencia clave está en manos de muy pocos miembros del equipo",
                recommendations_en=[
                    "Implement mandatory knowledge sharing sessions",
                    "Create comprehensive documentation for critical systems",
                    "Establish pair programming for knowledge transfer",
                    "Identify single points of failure and create backup expertise"
                ],
                recommendations_es=[
                    "Implementar sesiones obligatorias de intercambio de conocimientos",
                    "Crear documentación completa para sistemas críticos",
                    "Establecer programación en pareja para transferencia de conocimiento",
                    "Identificar puntos únicos de falla y crear experiencia de respaldo"
                ],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="attrition_signal",
                severity=SeverityLevel.HIGH,
                detected_at=timestamp,
                description_en="Loss of key knowledge holders would severely impact team capability",
                description_es="La pérdida de poseedores clave de conocimiento impactaría severamente la capacidad del equipo",
                recommendations_en=[
                    "Develop succession plans for critical roles",
                    "Cross-train team members on key systems",
                    "Improve retention strategies for key personnel"
                ],
                recommendations_es=[
                    "Desarrollar planes de sucesión para roles críticos",
                    "Capacitar a los miembros del equipo en sistemas clave",
                    "Mejorar las estrategias de retención para el personal clave"
                ],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="delivery_cadence",
                severity=SeverityLevel.MEDIUM,
                detected_at=timestamp,
                description_en="Delivery bottlenecks due to knowledge concentration",
                description_es="Cuellos de botella en la entrega debido a la concentración de conocimiento",
                recommendations_en=[
                    "Distribute code review responsibilities",
                    "Rotate team members across different areas"
                ],
                recommendations_es=[
                    "Distribuir las responsabilidades de revisión de código",
                    "Rotar a los miembros del equipo en diferentes áreas"
                ],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="workload_distribution",
                severity=SeverityLevel.LOW,
                detected_at=timestamp,
                description_en="Workload relatively balanced despite knowledge concentration",
                description_es="Carga de trabajo relativamente equilibrada a pesar de la concentración de conocimiento",
                recommendations_en=["Monitor for changes in workload patterns"],
                recommendations_es=["Monitorear cambios en los patrones de carga de trabajo"],
                signal_values=signals
            )
        ]
    
    def _generate_dependency_risks(
        self,
        team_id: str,
        signals: Dict[str, float],
        timestamp: datetime
    ) -> List[RiskRecord]:
        """Generate risks for dependency-heavy scenario."""
        analysis_id = f"analysis-{timestamp.strftime('%Y%m%d%H%M%S')}"
        
        return [
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="dependency_risk",
                severity=SeverityLevel.CRITICAL,
                detected_at=timestamp,
                description_en="Critical external dependencies blocking team progress",
                description_es="Dependencias externas críticas bloqueando el progreso del equipo",
                recommendations_en=[
                    "Map all external dependencies and their impact",
                    "Establish SLAs with dependent teams",
                    "Create fallback plans for critical dependencies",
                    "Consider architectural changes to reduce coupling"
                ],
                recommendations_es=[
                    "Mapear todas las dependencias externas y su impacto",
                    "Establecer SLAs con equipos dependientes",
                    "Crear planes de contingencia para dependencias críticas",
                    "Considerar cambios arquitectónicos para reducir el acoplamiento"
                ],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="delivery_cadence",
                severity=SeverityLevel.HIGH,
                detected_at=timestamp,
                description_en="Delivery delays caused by waiting on external dependencies",
                description_es="Retrasos en la entrega causados por esperar dependencias externas",
                recommendations_en=[
                    "Prioritize work that can be completed independently",
                    "Improve coordination with dependent teams",
                    "Build mock interfaces to unblock development"
                ],
                recommendations_es=[
                    "Priorizar el trabajo que se puede completar de forma independiente",
                    "Mejorar la coordinación con equipos dependientes",
                    "Construir interfaces simuladas para desbloquear el desarrollo"
                ],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="workload_distribution",
                severity=SeverityLevel.MEDIUM,
                detected_at=timestamp,
                description_en="Uneven workload due to dependency bottlenecks",
                description_es="Carga de trabajo desigual debido a cuellos de botella de dependencias",
                recommendations_en=[
                    "Reassign blocked work temporarily",
                    "Identify alternative tasks for blocked team members"
                ],
                recommendations_es=[
                    "Reasignar temporalmente el trabajo bloqueado",
                    "Identificar tareas alternativas para miembros del equipo bloqueados"
                ],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="knowledge_concentration",
                severity=SeverityLevel.LOW,
                detected_at=timestamp,
                description_en="Knowledge distribution is adequate for current dependency landscape",
                description_es="La distribución del conocimiento es adecuada para el panorama de dependencias actual",
                recommendations_en=["Continue current knowledge sharing practices"],
                recommendations_es=["Continuar las prácticas actuales de intercambio de conocimientos"],
                signal_values=signals
            )
        ]
    
    def _generate_attrition_risks(
        self,
        team_id: str,
        signals: Dict[str, float],
        timestamp: datetime
    ) -> List[RiskRecord]:
        """Generate risks for attrition warning scenario."""
        analysis_id = f"analysis-{timestamp.strftime('%Y%m%d%H%M%S')}"
        
        return [
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="attrition_signal",
                severity=SeverityLevel.CRITICAL,
                detected_at=timestamp,
                description_en="Critical attrition warning - multiple indicators suggest team members may leave",
                description_es="Advertencia crítica de desgaste - múltiples indicadores sugieren que los miembros del equipo pueden irse",
                recommendations_en=[
                    "Conduct urgent one-on-one meetings with all team members",
                    "Review compensation and benefits immediately",
                    "Assess work-life balance and workload concerns",
                    "Identify and address sources of dissatisfaction",
                    "Create retention plan for key team members"
                ],
                recommendations_es=[
                    "Realizar reuniones individuales urgentes con todos los miembros del equipo",
                    "Revisar compensación y beneficios inmediatamente",
                    "Evaluar el equilibrio trabajo-vida y las preocupaciones de carga de trabajo",
                    "Identificar y abordar las fuentes de insatisfacción",
                    "Crear plan de retención para miembros clave del equipo"
                ],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="workload_distribution",
                severity=SeverityLevel.HIGH,
                detected_at=timestamp,
                description_en="High workload contributing to attrition risk",
                description_es="Alta carga de trabajo contribuyendo al riesgo de desgaste",
                recommendations_en=[
                    "Reduce workload immediately",
                    "Ensure team takes scheduled time off",
                    "Reassess project commitments"
                ],
                recommendations_es=[
                    "Reducir la carga de trabajo inmediatamente",
                    "Asegurar que el equipo tome el tiempo libre programado",
                    "Reevaluar los compromisos del proyecto"
                ],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="knowledge_concentration",
                severity=SeverityLevel.MEDIUM,
                detected_at=timestamp,
                description_en="Knowledge concentration increases risk if attrition occurs",
                description_es="La concentración de conocimiento aumenta el riesgo si ocurre desgaste",
                recommendations_en=[
                    "Accelerate knowledge transfer initiatives",
                    "Document critical processes urgently"
                ],
                recommendations_es=[
                    "Acelerar las iniciativas de transferencia de conocimiento",
                    "Documentar procesos críticos urgentemente"
                ],
                signal_values=signals
            ),
            RiskRecord(
                analysis_id=analysis_id,
                team_id=team_id,
                dimension="delivery_cadence",
                severity=SeverityLevel.LOW,
                detected_at=timestamp,
                description_en="Delivery cadence stable but may be affected if attrition occurs",
                description_es="La cadencia de entrega es estable pero puede verse afectada si ocurre desgaste",
                recommendations_en=["Prepare contingency plans for potential team changes"],
                recommendations_es=["Preparar planes de contingencia para posibles cambios en el equipo"],
                signal_values=signals
            )
        ]
    
    def _clamp(self, value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
        """Clamp value to specified range."""
        return max(min_val, min(max_val, value))
