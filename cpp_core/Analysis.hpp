#pragma once

#include <string>
#include <vector>
#include <numeric>
#include <cmath>
#include <random>

namespace SatTrade {

class NeuralAnalyzer {
public:
    static double compute_anomaly_sigma(const std::vector<double>& observations, double current_value) {
        if (observations.empty()) return 0.0;
        double sum = std::accumulate(observations.begin(), observations.end(), 0.0);
        double mean = sum / observations.size();
        double sq_sum = std::inner_product(observations.begin(), observations.end(), observations.begin(), 0.0);
        double stdev = std::sqrt(sq_sum / observations.size() - mean * mean);
        if (stdev < 0.0001) return 0.0;
        return (current_value - mean) / stdev;
    }

    static double calculate_conviction(double gtfi, double sigma) {
        return std::tanh(std::abs(sigma) * gtfi);
    }

    /**
     * Institutional Monte Carlo VaR (Value at Risk)
     * Estimates potential loss at 99% confidence interval.
     */
    static double calculate_var_99(double portfolio_value, double volatility, double horizon_days = 1.0) {
        const int SIMULATIONS = 10000;
        std::default_random_engine generator;
        std::normal_distribution<double> distribution(0.0, volatility * std::sqrt(horizon_days / 252.0));

        std::vector<double> results;
        for (int i = 0; i < SIMULATIONS; ++i) {
            double ret = distribution(generator);
            results.push_back(portfolio_value * ret);
        }

        std::sort(results.begin(), results.end());
        // 1st percentile for 99% VaR
        return std::abs(results[SIMULATIONS / 100]);
    }
};

/**
 * Lock-Free Ring Buffer for HFT Signal Processing
 */
template<typename T, size_t Size>
class LockFreeQueue {
public:
    bool push(const T& item) {
        size_t head = head_.load(std::memory_order_relaxed);
        size_t next_head = (head + 1) % Size;
        if (next_head == tail_.load(std::memory_order_acquire)) return false;
        buffer_[head] = item;
        head_.store(next_head, std::memory_order_release);
        return true;
    }

    bool pop(T& item) {
        size_t tail = tail_.load(std::memory_order_relaxed);
        if (tail == head_.load(std::memory_order_acquire)) return false;
        item = buffer_[tail];
        tail_.store((tail + 1) % Size, std::memory_order_release);
        return true;
    }

private:
    T buffer_[Size];
    std::atomic<size_t> head_{0};
    std::atomic<size_t> tail_{0};
};

} // namespace SatTrade
