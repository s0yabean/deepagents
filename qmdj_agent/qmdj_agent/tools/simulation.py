"""Simulation tools for the QMDJ agent."""

from langchain_core.tools import tool
import random
import statistics

@tool(parse_docstring=True)
def run_monte_carlo_simulation(base_probability: int, volatility: str, energy_factor: float = 1.0) -> str:
    """Run a Monte Carlo simulation to determine the probability distribution of outcomes.
    
    Args:
        base_probability: The estimated probability of success (0-100).
        volatility: The volatility of the situation ('Low', 'Medium', 'High').
        energy_factor: A multiplier based on palace energy (e.g., 0.2 for weak, 2.0 for strong).
    """
    iterations = 1000
    results = []
    
    # Map volatility to standard deviation
    vol_map = {
        "Low": 10,
        "Medium": 20,
        "High": 35
    }
    std_dev = vol_map.get(volatility, 20)
    
    # Adjust base probability by energy factor (simplified logic)
    # If energy is high (>1.0), it amplifies the base signal (whether good or bad)
    # If energy is low (<1.0), it dampens the signal
    
    # Center the probability around 0 (-50 to +50) for amplification logic
    centered_prob = base_probability - 50
    amplified_prob = centered_prob * energy_factor
    final_mean = amplified_prob + 50
    
    # Clamp mean between 5 and 95
    final_mean = max(5, min(95, final_mean))
    
    for _ in range(iterations):
        # Generate random outcome based on normal distribution
        outcome = random.gauss(final_mean, std_dev)
        # Clamp outcome between 0 and 100
        outcome = max(0, min(100, outcome))
        results.append(outcome)
    
    # Analyze results
    success_count = sum(1 for r in results if r >= 50)
    success_prob = (success_count / iterations) * 100
    
    mean_outcome = statistics.mean(results)
    median_outcome = statistics.median(results)
    
    # Determine risk level
    risk_level = "Low"
    if success_prob < 50:
        risk_level = "High"
    elif volatility == "High":
        risk_level = "Medium-High"
    
    return f"""**Monte Carlo Simulation Results ({iterations} runs):**
- Mean Outcome Score: {mean_outcome:.1f}/100
- Median Outcome Score: {median_outcome:.1f}/100
- Probability of Success (>50 score): {success_prob:.1f}%
- Volatility Setting: {volatility} (Std Dev: {std_dev})
- Energy Factor Applied: {energy_factor}x

**Distribution:**
- Best Case (95th percentile): {sorted(results)[int(iterations*0.95)]:.1f}
- Worst Case (5th percentile): {sorted(results)[int(iterations*0.05)]:.1f}

**Risk Assessment:**
- Risk Level: {risk_level}
"""
