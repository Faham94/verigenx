from VeriGenX.agents.wavewhisperer.vcd_reader import VCDReader
from VeriGenX.agents.wavewhisperer.anomaly_detector import AnomalyDetector
from VeriGenX.agents.wavewhisperer.explainer import WaveExplainer
from VeriGenX.agents.wavewhisperer.report_gen import WaveReportGenerator
from typing import Dict, Any, List

class WaveWhisperer:
    def __init__(self, design_name: str, test_plan: Dict[str, Any]):
        self.design_name = design_name
        self.test_plan = test_plan
        self.detector = AnomalyDetector(design_name, test_plan)
        self.explainer = WaveExplainer()
        self.reporter = WaveReportGenerator(design_name)

    def analyze_vcd(self, vcd_path: str, output_html_path: str) -> List[Dict[str, Any]]:
        """
        Runs the full waveform analysis flow:
        1. Reads and parses VCD waveform into continuous time series
        2. Applies timing/FSM/protocol/reset checks to identify anomalies
        3. Invokes the LLM explanation engine to detail root cause and suggest fixes
        4. Writes an interactive standalone Plotly-based HTML report
        """
        reader = VCDReader(vcd_path)
        df = reader.parse()
        
        raw_anomalies = self.detector.detect_anomalies(df)
        
        explained_anomalies = self.explainer.explain_anomalies(self.design_name, raw_anomalies, self.test_plan)
        
        self.reporter.generate_html_report(df, explained_anomalies, output_html_path)
        
        return explained_anomalies
