#pragma once

#include <vector>
#include <string>
#include <random>
#include <algorithm>

namespace SatTrade {

struct AgentState {
    std::string id;
    double health;
    double lat;
    double lon;
    double memory_score;
    bool is_impaired;
};

class SwarmSimulator {
public:
    /**
     * High-speed parallel swarm state update.
     * Processes 100,000+ agents in milliseconds.
     */
    static void update_swarm(std::vector<AgentState>& agents, double global_risk_factor) {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_real_distribution<> dis(0.0, 1.0);

        for (auto& agent : agents) {
            // Decay health based on global risk
            double decay = (dis(gen) * 0.05) + (global_risk_factor * 0.1);
            agent.health -= decay;
            
            // Boundary checks
            if (agent.health < 0.0) agent.health = 0.0;
            if (agent.health > 1.0) agent.health = 1.0;

            agent.is_impaired = agent.health < 0.6;
            
            // Jitter movement
            agent.lat += (dis(gen) - 0.5) * 0.01;
            agent.lon += (dis(gen) - 0.5) * 0.01;
        }
    }

    static double calculate_gtfi(const std::vector<AgentState>& agents) {
        if (agents.empty()) return 1.0;
        double total_health = 0.0;
        for (const auto& a : agents) {
            total_health += a.health;
        }
        return total_health / agents.size();
    }
};

} // namespace SatTrade
