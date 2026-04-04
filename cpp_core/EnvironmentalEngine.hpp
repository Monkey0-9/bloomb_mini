#pragma once

#include <string>
#include <vector>

namespace SatTrade {

struct WeatherSignal {
    double lat;
    double lon;
    double wind_speed;
    int condition_code;
};

class EnvironmentalEngine {
public:
    /**
     * Compute Systemic Weather Risk across a fleet segment.
     */
    static double calculate_systemic_risk(const std::vector<WeatherSignal>& signals) {
        if (signals.empty()) return 0.0;
        
        double total_risk = 0.0;
        for (const auto& s : signals) {
            // Critical Wind Threshold: 30 knots
            if (s.wind_speed > 30.0) {
                total_risk += (s.wind_speed - 30.0) / 70.0; // Normalized impact
            }
        }
        
        return std::min(1.0, total_risk / signals.size());
    }
};

} // namespace SatTrade
