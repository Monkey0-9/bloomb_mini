#include "Engine.hpp"
#include "Options.hpp"
#include "Analysis.hpp"
#include "Monitor.hpp"
#include "BehavioralPredictor.hpp"
#include "SpatialEngine.hpp"
#include "SwarmSimulator.hpp"
#include <iomanip>
#include <csignal>
#include <algorithm>
#include <iostream>
#include <vector>
#include <map>
#include <thread>

using namespace SatTrade;

void display_header() {
    std::cout << "\033[2J\033[H"; // Clear screen
    std::cout << "\033[1;36m================================================================================\033[0m" << std::endl;
    std::cout << "\033[1;37m   SAT-TRADE ALPHA-PRIME v3.0 // MIROFISH PREDICTIVE INTELLIGENCE TERMINAL     \033[0m" << std::endl;
    std::cout << "\033[1;36m================================================================================\033[0m" << std::endl;
}

void display_market_data(const std::map<std::string, double>& prices) {
    std::cout << "\033[1;33m[LIVE MARKET DATA]\033[0m" << std::endl;
    std::cout << "--------------------------------------------------------------------------------" << std::endl;
    for (const auto& [ticker, price] : prices) {
        double volatility = 0.2 + (rand() % 10) / 100.0;
        double call_price = OptionsEngine::calculate_black_scholes(price, price * 1.05, 0.1, 0.05, volatility, true);

        std::cout << std::left << std::setw(8) << ticker 
                  << " | PRICE: \033[1;32m" << std::fixed << std::setprecision(2) << price << "\033[0m" 
                  << " | CALL: " << std::setprecision(3) << call_price
                  << " | VOL: " << (rand() % 1000000) << std::endl;
    }
    std::cout << "--------------------------------------------------------------------------------" << std::endl;
}

void display_predictions(const std::vector<BehavioralOutcome>& predictions) {
    std::cout << "\033[1;34m[MIROFISH PREDICTIVE SWARM DIVERGENCE]\033[0m" << std::endl;
    for (const auto& p : predictions) {
        std::cout << " > " << std::setw(6) << p.ticker 
                  << " | IMPACT: " << (p.predicted_impact > 0.5 ? "\033[1;31mHIGH\033[0m" : "LOW")
                  << " | VAR: " << std::setprecision(3) << p.predicted_impact
                  << " | PROB: " << std::fixed << std::setprecision(1) << p.probability * 100 << "%"
                  << std::endl;
    }
    std::cout << "--------------------------------------------------------------------------------" << std::endl;
}

int main() {
    AlphaEngine engine;
    OMS oms;

    engine.start();
    SystemMonitor::log_system_health();
    
    std::map<std::string, double> mock_prices = {
        {"AAPL", 175.43}, {"MSFT", 420.12}, {"MT", 28.50}, {"ZIM", 12.30}, {"XOM", 112.90}
    };
    std::vector<std::string> tickers = {"AAPL", "MSFT", "MT", "ZIM", "XOM"};

    bool running = true;
    while (running) {
        auto frame_start = std::chrono::steady_clock::now();
        display_header();
        
        double gtfi = engine.get_gtfi();
        std::cout << "\033[1;35m[GLOBAL TRADE FLOW INDEX]\033[0m GTFI: " 
                  << std::setprecision(4) << gtfi << " "
                  << (gtfi < 0.9 ? "\033[1;31m[SYSTEMIC DISRUPTION]\033[0m" : "\033[1;32m[OPTIMAL]\033[0m")
                  << std::endl << std::endl;

        display_market_data(mock_prices);

        // Advanced Predictive Block
#include "Engine.hpp"
#include "Options.hpp"
#include "Analysis.hpp"
#include "Monitor.hpp"
#include "BehavioralPredictor.hpp"
#include "EnvironmentalEngine.hpp"

// ... inside main loop
        double signal_sigma = NeuralAnalyzer::compute_anomaly_sigma({110, 115, 120, 118}, 145);
        auto predictions = BehavioralPredictor::predict_swarm_divergence(gtfi, signal_sigma, tickers);
        
        // Systemic Environmental Risk
        double env_risk = EnvironmentalEngine::calculate_systemic_risk({{30.5, 32.3, 35.5, 201}});
        
        display_predictions(predictions);
        std::cout << "\033[1;36m[ENVIRONMENTAL RISK]\033[0m SYSTEMIC_WEATHER_IMPACT: " << env_risk * 100 << "%" << std::endl;
        
        std::cout << "\033[1;37m[OMS STATUS] COMMANDS: (B)uy (S)ell (O)ption-Put (C)all (Q)uit\033[0m" << std::endl;
        SystemMonitor::log_latency("FRAME_TRANSITION", frame_start);
        
        std::cout << "> ";
        std::this_thread::sleep_for(std::chrono::seconds(1));
        
        engine.update_signal("SATELLITE_FEED_NRT", (rand() % 20) / 100.0);
        for (auto& [t, p] : mock_prices) p += (rand() % 100 - 50) / 100.0;
    }

    engine.stop();
    return 0;
}
