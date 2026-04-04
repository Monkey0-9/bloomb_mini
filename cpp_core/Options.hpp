#pragma once

#include <cmath>
#include <algorithm>

namespace SatTrade {

struct Greeks {
    double delta;
    double gamma;
    double vega;
    double theta;
    double rho;
};

class OptionsEngine {
public:
    static double calculate_black_scholes(double S, double K, double T, double r, double v, bool is_call) {
        double d1 = (std::log(S / K) + (r + v * v / 2.0) * T) / (v * std::sqrt(T));
        double d2 = d1 - v * std::sqrt(T);

        if (is_call) {
            return S * cumulative_normal_distribution(d1) - K * std::exp(-r * T) * cumulative_normal_distribution(d2);
        } else {
            return K * std::exp(-r * T) * cumulative_normal_distribution(-d2) - S * cumulative_normal_distribution(-d1);
        }
    }

    /**
     * Institutional Greeks Calculation
     */
    static Greeks calculate_greeks(double S, double K, double T, double r, double v, bool is_call) {
        double d1 = (std::log(S / K) + (r + v * v / 2.0) * T) / (v * std::sqrt(T));
        double d2 = d1 - v * std::sqrt(T);
        double n_prime_d1 = (1.0 / std::sqrt(2.0 * M_PI)) * std::exp(-0.5 * d1 * d1);

        Greeks g;
        if (is_call) {
            g.delta = cumulative_normal_distribution(d1);
            g.theta = (-S * n_prime_d1 * v / (2.0 * std::sqrt(T)) - r * K * std::exp(-r * T) * cumulative_normal_distribution(d2)) / 365.0;
        } else {
            g.delta = cumulative_normal_distribution(d1) - 1.0;
            g.theta = (-S * n_prime_d1 * v / (2.0 * std::sqrt(T)) + r * K * std::exp(-r * T) * cumulative_normal_distribution(-d2)) / 365.0;
        }

        g.gamma = n_prime_d1 / (S * v * std::sqrt(T));
        g.vega = (S * std::sqrt(T) * n_prime_d1) / 100.0;
        g.rho = (K * T * std::exp(-r * T) * (is_call ? cumulative_normal_distribution(d2) : -cumulative_normal_distribution(-d2))) / 100.0;

        return g;
    }

private:
    static double cumulative_normal_distribution(double x) {
        return 0.5 * std::erfc(-x * std::sqrt(0.5));
    }
};

} // namespace SatTrade
