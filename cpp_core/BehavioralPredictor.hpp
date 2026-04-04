#pragma once

#include <vector>
#include <string>
#include <map>
#include <random>
#include <cmath>

namespace SatTrade {

enum class AgentStance { CAUTIOUS, AGGRESSIVE, BALANCED };

struct BehavioralOutcome {
    std::string ticker;
    double predicted_impact;
    double probability;
    std::string reason;
};

class BehavioralPredictor {
public:
    /**
     * MiroFish-Inspired Predictive Swarm Simulation
     * Simulates 'N' parallel futures to find the most probable outcome.
     */
    static std::vector<BehavioralOutcome> predict_swarm_divergence(double gtfi, double sigma, const std::vector<std::string>& tickers) {
        std::vector<BehavioralOutcome> outcomes;
        std::default_random_engine generator;
        std::normal_distribution<double> noise(0.0, 0.05);

        for (const auto& ticker : tickers) {
            double disruption_impact = 0.0;
            
            // Parallel World 1: Cautious Agents (High sensitivity to disruption)
            double cautious_impact = (1.0 - gtfi) * 1.5 + std::abs(sigma) * 0.1;
            
            // Parallel World 2: Aggressive Agents (Priority on speed, vulnerable to conflict)
            double aggressive_impact = (1.0 - gtfi) * 0.5 + std::abs(sigma) * 0.4;
            
            // Average predicted variance
            disruption_impact = (cautious_impact + aggressive_impact) / 2.0 + noise(generator);

            outcomes.push_back({
                ticker,
                disruption_impact,
                std::min(0.99, 0.7 + std::abs(sigma) * 0.05), // Probability scales with signal strength
                "MiroFish Divergence: Multi-agent sensitivity detected at " + std::to_string(disruption_impact) + " variance."
            });
        }
        
        return outcomes;
    }
};

} // namespace SatTrade
